import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Assuming your Flask app is created in main.py and named 'app'
from main import app
from database.db import db
from model.models import Actividades, Inscripciones, EstadoActividad, Organizaciones, Usuarios, PerfilesUsuario
from services.recommendation_service import obtener_features, predecir_participacion

# Helper function to create a dummy organization if needed by activities
def create_dummy_org(org_id=1, nombre_org="Dummy Org"):
    org = Organizaciones.query.get(org_id)
    if not org:
        org = Organizaciones(id_organizacion=org_id, nombre_org=nombre_org, descripcion="Test", contacto="test@example.com")
        db.session.add(org)
        db.session.commit()
    return org

# Helper function to create a dummy user if needed by organization
def create_dummy_user_for_org(user_id=1, org_id=1):
    user = Usuarios.query.get(user_id)
    if not user:
        perfil = PerfilesUsuario.query.filter_by(nombre_perfil='organizador').first()
        if not perfil:
            perfil = PerfilesUsuario(id_perfil=2, nombre_perfil='organizador') # Assuming 2 is organizer
            db.session.add(perfil)
            db.session.commit()

        user = Usuarios(id_usuario=user_id, nombre="Test Org User", email=f"orguser{user_id}@example.com", id_perfil=perfil.id_perfil, id_organizacion_predeterminada=org_id)
        user.set_password("password") # Assuming a set_password method
        db.session.add(user)
        db.session.commit()
    return user

class TestObtenerFeatures(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms if any part of app setup needs it
        db.create_all()

        # Create a dummy organization and user for it, as Actividades might require id_organizacion
        self.org = create_dummy_org(org_id=1)
        # self.org_user = create_dummy_user_for_org(user_id=1, org_id=self.org.id_organizacion)


        self.actividad1 = Actividades(id_actividad=1, nombre="Test Actividad 1", cupo_maximo=20, estado=EstadoActividad.ABIERTO, id_organizacion=self.org.id_organizacion)
        self.actividad2 = Actividades(id_actividad=2, nombre="Test Actividad 2", cupo_maximo=5, estado=EstadoActividad.ABIERTO, id_organizacion=self.org.id_organizacion)
        db.session.add_all([self.actividad1, self.actividad2])
        db.session.commit()

        self.inscripcion1_act1 = Inscripciones(id_usuario=1, id_actividad=1) # Assuming user with id 1 exists or FK is not enforced strictly in SQLite for this
        self.inscripcion2_act1 = Inscripciones(id_usuario=2, id_actividad=1) # Assuming user with id 2 exists
        db.session.add_all([self.inscripcion1_act1, self.inscripcion2_act1])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_activity_exists_with_inscriptions(self):
        features = obtener_features(1)
        self.assertIsNotNone(features)
        self.assertEqual(features['current_inscriptions'], 2)
        self.assertEqual(features['cupo_maximo'], 20)
        self.assertEqual(features['historico_similar'], 0.5)
        self.assertEqual(features['habilidades_voluntarios'], 3)

    def test_activity_exists_no_inscriptions(self):
        features = obtener_features(2) # actividad2 has no inscriptions
        self.assertIsNotNone(features)
        self.assertEqual(features['current_inscriptions'], 0)
        self.assertEqual(features['cupo_maximo'], 5)
        self.assertEqual(features['historico_similar'], 0.5)
        self.assertEqual(features['habilidades_voluntarios'], 3)

    def test_activity_does_not_exist(self):
        features = obtener_features(999) # Non-existent ID
        self.assertIsNone(features)

class TestPredecirParticipacion(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        db.create_all()

        self.org = create_dummy_org(org_id=1)
        # self.org_user = create_dummy_user_for_org(user_id=1, org_id=self.org.id_organizacion)

        for i in range(15):
            act = Actividades(
                id_actividad=i+1,
                nombre=f"Activity {i+1}",
                cupo_maximo=10,
                estado=EstadoActividad.ABIERTO,
                id_organizacion=self.org.id_organizacion
            )
            db.session.add(act)
            if i < 10: # Ensure at least 10 activities have varied inscriptions for robust training
                num_inscripciones = (i % 5) + 1 # 1 to 5 inscriptions
                if i < 3 and num_inscripciones < 6 : # ensure some activities have high participation (>=60%)
                    num_inscripciones = 7
                elif i >=3 and i < 6 and num_inscripciones >=6: # ensure some activities have low participation
                     num_inscripciones = 2


                for j in range(num_inscripciones):
                    # We need dummy users for inscriptions if FK is enforced.
                    # For simplicity, assuming user IDs 1-5 are implicitly valid for this test context
                    # or not strictly enforced by SQLite in this setup.
                    ins = Inscripciones(id_usuario=j+1, id_actividad=i+1)
                    db.session.add(ins)
        db.session.commit()
        self.target_activity_id_sufficient_data = 1
        self.target_activity_id_less_data = 12 # one of the activities with fewer inscriptions for variety

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_basic_prediction_run(self):
        prediction = predecir_participacion(self.target_activity_id_sufficient_data)
        self.assertIsNotNone(prediction)
        self.assertIn('probabilidad', prediction)
        self.assertIn('metricas', prediction)
        self.assertIn('tree_dot_file', prediction) # Check for tree file key

        if 'error' not in prediction: # Proceed if no error
            self.assertTrue(0 <= prediction['probabilidad'] <= 1)
            if prediction['metricas'] and isinstance(prediction['metricas'], dict):
                 self.assertIn('accuracy', prediction['metricas'])
            self.assertIsNotNone(prediction['tree_dot_file']) # tree.dot should be generated
        else:
            print(f"Prediction error/info in basic run: {prediction.get('error') or prediction.get('info')}")


    def test_prediction_insufficient_data_scenario(self):
        # Clean slate for this specific test to ensure only one activity exists
        db.session.remove()
        db.drop_all()
        db.create_all()

        org = create_dummy_org(org_id=99) # Fresh org
        act = Actividades(id_actividad=100, nombre="Lone Activity", cupo_maximo=10, estado=EstadoActividad.ABIERTO, id_organizacion=org.id_organizacion)
        db.session.add(act)
        # Add a few inscriptions, but not enough to create two classes or pass MIN_SAMPLES
        ins = Inscripciones(id_usuario=1, id_actividad=100)
        db.session.add(ins)
        db.session.commit()

        prediction = predecir_participacion(100)
        self.assertIsNotNone(prediction)
        self.assertIn('info', prediction)
        # The exact message from predecir_participacion when MIN_SAMPLES_FOR_TRAINING is not met or only one class.
        # Current message: f"Datos insuficientes para entrenar el modelo. Muestras: {len(X_df)}, Clases: {len(y_series.unique()) if X_data else 0}."
        # Followed by: "Default prediction. Samples: {len(X_df)}, Classes: {len(y_series.unique()) if X_data else 0}" in the dict.
        # For a single activity, X_df will have 1 sample. y_series will have 1 sample, 1 class.
        expected_info_msg = "Default prediction. Samples: 1, Classes: 1"
        self.assertEqual(prediction['info'], expected_info_msg)
        self.assertEqual(prediction['probabilidad'], 0.0) # Default is y_series.mean() which is 0 or 1 for a single class. If cupo=10, ins=1 -> 10% occ -> y=0. So mean is 0.
        self.assertIsNone(prediction['tree_dot_file']) # No tree should be generated

    def test_prediction_activity_not_found(self):
        prediction = predecir_participacion(999) # Non-existent ID
        self.assertIsNotNone(prediction)
        self.assertIn('error', prediction)
        self.assertEqual(prediction['error'], "Activity features not found.")

if __name__ == '__main__':
    unittest.main()
