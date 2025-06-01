import os
from flask import Flask
from database.db import db, init_app
from controller.routes import main_bp
from controller.auth_routes import auth_bp
from controller.dashboard_routes import dashboard_bp
from flask_login import LoginManager
from flask_migrate import Migrate # Import Migrate
from model.models import Usuarios # Changed User to Usuarios
from database.datos_iniciales import seed_data # Added import for seed_data


app = Flask(__name__, instance_relative_config=True, template_folder='view/templates') # Enable instance folder

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_replace_me_if_not_using_env_or_secrets')
default_sqlite_uri = f"sqlite:///{os.path.join(app.instance_path, 'konectai.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_sqlite_uri)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure the instance folder exists for SQLite fallback
try:
    os.makedirs(app.instance_path)
except OSError:
    pass # Already exists or other error (Flask handles some of this)

# Initialize extensions with the app instance
init_app(app) # Initialize SQLAlchemy (from database.db)
migrate = Migrate(app, db) # Initialize Flask-Migrate

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login' # Route name for the login page (blueprint_name.view_function_name)
login_manager.login_message_category = 'info' # Flash message category

@login_manager.user_loader
def load_user(user_id):
    return Usuarios.query.get(int(user_id))

# Register Blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp) # Register the dashboard blueprint

@app.cli.command('create-db')
def create_db_command():
    """Creates the database tables."""
    with app.app_context():
        import model.models # Ensure all models are imported
        db.create_all()
    print('Database tables created.')

@app.cli.command('seed-db')
def seed_db_command():
    """Seeds the database with initial data."""
    with app.app_context():
        seed_data()
    # The print statement is now inside seed_data() from datos_iniciales.py
    # print('Database seeded with initial data.') # This can be removed or kept if preferred

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
