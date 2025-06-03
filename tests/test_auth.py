import unittest
import os
from main import app  # Import the Flask app instance from main.py
from database.db import db
from model.models import Usuarios, Discapacidades, Preferencias, UsuarioDiscapacidad, TipoDiscapacidad, EstadoUsuario
from datetime import datetime

# It's good practice to set a specific test database URI
TEST_DB_URI = 'sqlite:///:memory:'
# Or use a file-based SQLite for inspection:
# TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test.db')
# TEST_DB_URI = f'sqlite:///{TEST_DB_PATH}'


class AuthTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # This runs once before all tests in this class
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = TEST_DB_URI
        # app.config['SERVER_NAME'] = 'localhost.test' # Usually not needed for basic tests

        # If using a file-based test DB and want to clean it up before tests
        # if os.path.exists(TEST_DB_PATH):
        #     os.remove(TEST_DB_PATH)

    def setUp(self):
        # This runs before each test method
        self.app_context = app.app_context()
        self.app_context.push() # Push an application context
        db.create_all()
        self.client = app.test_client()

        # Seed initial Discapacidades and Preferencias for testing
        # Ensure enum values are correctly used if 'nombre' is an Enum
        dis1 = Discapacidades(nombre=TipoDiscapacidad.AUDITIVA, descripcion="Auditiva")
        dis2 = Discapacidades(nombre=TipoDiscapacidad.VISUAL, descripcion="Visual")
        db.session.add_all([dis1, dis2])

        pref1 = Preferencias(nombre_corto="Tecnología", descripcion_detallada="Interés en tecnología")
        pref2 = Preferencias(nombre_corto="Medio Ambiente", descripcion_detallada="Interés en medio ambiente")
        db.session.add_all([pref1, pref2])
        db.session.commit()

        self.discapacidad1_id = dis1.id_discapacidad
        self.preferencia1_id = pref1.id_preferencia


    def tearDown(self):
        # This runs after each test method
        db.session.remove()
        db.drop_all()
        self.app_context.pop() # Pop the application context

    # --- Registration Tests ---
    def test_successful_registration(self):
        data = {
            'dni': '12345678',
            'nombre': 'Test User',
            'password': 'password123',
            'confirm_password': 'password123',
            'perfil': 'voluntario',
            'estado_usuario': 'activo', # This should come from the form; ensure it's handled
            'acepto_politica': True,
            'discapacidades': [str(self.discapacidad1_id)],
            'preferencias': [str(self.preferencia1_id)]
        }
        response = self.client.post('/auth/register', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Should redirect to login, then login page is 200
        self.assertIn(b'Por favor Inicia Sesi', response.data) # Flash message after registration

        user = Usuarios.query.filter_by(DNI='12345678').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.nombre, 'Test User')
        self.assertEqual(user.perfil.value if hasattr(user.perfil, 'value') else user.perfil, 'voluntario') # Handle enum
        self.assertEqual(user.estado_usuario.value if hasattr(user.estado_usuario, 'value') else user.estado_usuario, 'activo') # Handle enum
        self.assertTrue(user.check_password('password123'))

        # Check relationships
        self.assertEqual(len(user.discapacidades_pivot), 1)
        self.assertEqual(user.discapacidades_pivot[0].id_discapacidad, self.discapacidad1_id)
        self.assertEqual(len(user.preferencias), 1)
        self.assertEqual(user.preferencias[0].id_preferencia, self.preferencia1_id)

    def test_registration_missing_dni(self):
        data = { # DNI is missing
            'nombre': 'Test User', 'password': 'password123', 'confirm_password': 'password123',
            'perfil': 'voluntario', 'acepto_politica': True
        }
        response = self.client.post('/auth/register', data=data)
        self.assertEqual(response.status_code, 200) # Form redisplayed
        self.assertIn(b'This field is required.', response.data) # Default WTForms error
        # Or check for specific label: self.assertIn(b'DNI', response.data) followed by error
        user = Usuarios.query.filter_by(nombre='Test User').first()
        self.assertIsNone(user)

    def test_registration_missing_nombre(self):
        data = {
            'dni': '87654321', # Nombre is missing
            'password': 'password123', 'confirm_password': 'password123',
            'perfil': 'voluntario', 'acepto_politica': True
        }
        response = self.client.post('/auth/register', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'This field is required.', response.data)
        user = Usuarios.query.filter_by(DNI='87654321').first()
        self.assertIsNone(user)

    def test_registration_password_mismatch(self):
        data = {
            'dni': '11223344', 'nombre': 'Mismatch User',
            'password': 'password123', 'confirm_password': 'password321', # Mismatch
            'perfil': 'voluntario', 'acepto_politica': True
        }
        response = self.client.post('/auth/register', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Field must be equal to password.', response.data) # Default WTForms error for EqualTo

    def test_registration_privacy_policy_not_accepted(self):
        data = {
            'dni': '22334455', 'nombre': 'Privacy User',
            'password': 'password123', 'confirm_password': 'password123',
            'perfil': 'voluntario' # acepto_politica is missing or False
        }
        response = self.client.post('/auth/register', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Debe aceptar la pol', response.data) # Custom error message

    def test_registration_dni_already_exists(self):
        # First registration
        data1 = {
            'dni': '33445566', 'nombre': 'Original User', 'password': 'password123',
            'confirm_password': 'password123', 'perfil': 'voluntario', 'acepto_politica': True
        }
        self.client.post('/auth/register', data=data1, follow_redirects=True)

        # Attempt second registration with same DNI
        data2 = {
            'dni': '33445566', 'nombre': 'Duplicate User', 'password': 'password456',
            'confirm_password': 'password456', 'perfil': 'organizador', 'acepto_politica': True
        }
        response = self.client.post('/auth/register', data=data2)
        self.assertEqual(response.status_code, 200) # Should show form with error
        # This requires handling IntegrityError from SQLAlchemy and flashing a message,
        # or a custom validator in the form. Assuming a flash message or form error.
        # For now, we check if the second user wasn't created with the new name.
        user_duplicate = Usuarios.query.filter_by(nombre='Duplicate User').first()
        self.assertIsNone(user_duplicate)
        # A more specific check for the error message would be good here.
        # e.g. self.assertIn(b'DNI ya registrado', response.data) if such logic is added.
        # For now, the DNI unique constraint in model should prevent duplicate and cause an IntegrityError.
        # The test should ideally mock db.session.commit to catch the IntegrityError or the form should validate uniqueness.
        # As is, this test might pass if the commit fails silently in test mode or if error isn't shown to user.
        # For a robust test, the route should catch IntegrityError for DNI and show a form error.

    # --- Login Tests ---
    def _register_default_user(self, dni='12345678', password='password123'):
        user = Usuarios(DNI=dni, nombre='Login Test User', perfil='voluntario', estado_usuario=EstadoUsuario.ACTIVO)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def test_successful_login(self):
        self._register_default_user()
        login_data = {'dni': '12345678', 'password': 'password123'}
        response = self.client.post('/auth/login', data=login_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Assuming redirect to home ('/') which is 200
        self.assertIn(b'Inicio de sesi', response.data) # Success flash
        self.assertIn(b'Logout', response.data) # Assuming 'Logout' link appears on home for authenticated user

    def test_login_nonexistent_dni(self):
        login_data = {'dni': '00000000', 'password': 'password123'}
        response = self.client.post('/auth/login', data=login_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'verifica tu DNI y contrase', response.data) # Failure flash

    def test_login_incorrect_password(self):
        self._register_default_user(dni='11122233')
        login_data = {'dni': '11122233', 'password': 'wrongpassword'}
        response = self.client.post('/auth/login', data=login_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Stays on login page
        self.assertIn(b'verifica tu DNI y contrase', response.data) # Failure flash

    def test_login_empty_dni(self):
        login_data = {'dni': '', 'password': 'password123'}
        response = self.client.post('/auth/login', data=login_data)
        self.assertEqual(response.status_code, 200) # Form redisplayed
        self.assertIn(b'This field is required.', response.data) # WTForms error

    def test_login_empty_password(self):
        self._register_default_user(dni='22334455')
        login_data = {'dni': '22334455', 'password': ''}
        response = self.client.post('/auth/login', data=login_data)
        self.assertEqual(response.status_code, 200) # Form redisplayed
        self.assertIn(b'This field is required.', response.data) # WTForms error

    # --- Logout Test ---
    def test_logout(self):
        self._register_default_user()
        self.client.post('/auth/login', data={'dni': '12345678', 'password': 'password123'}, follow_redirects=True)

        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Assuming redirect to home
        self.assertIn(b'You have been logged out.', response.data) # Logout flash
        # Check if login link is present (user is logged out)
        self.assertIn(b'Login', response.data) # Assuming 'Login' link appears on home for logged out user

if __name__ == '__main__':
    unittest.main()
