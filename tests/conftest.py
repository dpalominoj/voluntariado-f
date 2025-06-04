# tests/conftest.py
import pytest
from flask import Flask
from database.db import db, init_app as init_db
from model.models import Usuarios, Actividades, Inscripciones, Recomendaciones, TipoRecomendacion, EstadoActividad, Organizaciones

@pytest.fixture(scope='session')
def app():
    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.secret_key = 'test_secret_key' # Needed for session stuff if any part of tested code uses it

    init_db(flask_app) # Initialize db with app

    with flask_app.app_context():
        db.create_all() # Create tables

    yield flask_app

    with flask_app.app_context():
        db.drop_all() # Clean up

@pytest.fixture(scope='function') # Use function scope for db to reset for each test
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def database(app):
    with app.app_context():
        # Clean out tables before each test
        db.session.query(Recomendaciones).delete()
        db.session.query(Inscripciones).delete()
        db.session.query(Actividades).delete()
        db.session.query(Usuarios).delete()
        db.session.query(Organizaciones).delete()
        db.session.commit()
        yield db
        # Clean up again after test (optional, as drop_all in app fixture handles final cleanup)
        db.session.rollback() # Rollback any uncommitted changes
        db.session.query(Recomendaciones).delete()
        db.session.query(Inscripciones).delete()
        db.session.query(Actividades).delete()
        db.session.query(Usuarios).delete()
        db.session.query(Organizaciones).delete()
        db.session.commit()
