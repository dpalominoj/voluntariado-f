from flask import Blueprint, render_template
from flask_login import current_user # Import current_user
from model.models import Actividades, Usuarios # Updated imports
from services.prediction_service import get_compatibility_scores # Import the service

main_bp = Blueprint('main', __name__, template_folder='../view/templates')

@main_bp.route('/')
def home():
    """Serves the home page."""
    return render_template('home.html')

@main_bp.route('/programs')
def programs():
    """Serves the page listing all programs."""
    all_programs = Actividades.query.all() # Changed Program to Actividades
    compatibility_scores = {}

    if current_user.is_authenticated and current_user.perfil == 'voluntario': # Changed role to perfil, 'Volunteer' to 'voluntario'
        # Create a dummy user profile for now - this would come from the User model or a more detailed profile
        user_profile_data = {
            'id': current_user.id_usuario, # Changed current_user.id to current_user.id_usuario
            'username': current_user.nombre, # Changed current_user.username to current_user.nombre
            'interests': ['environment', 'education', 'animals'], # Example interests
            'skills': ['writing', 'gardening'] # Example skills
        }
        
        # Prepare program data for the service
        program_data_for_service = [
            {'id': p.id_actividad, 'name': p.nombre, 'description': p.descripcion, 'category': p.nombre.lower() if p.nombre else ""} # Updated fields
            for p in all_programs
        ]
        
        if program_data_for_service:
            compatibility_scores = get_compatibility_scores(user_profile_data, program_data_for_service)

    return render_template('programs.html', programs=all_programs, compatibility_scores=compatibility_scores)

@main_bp.route('/help')
def help_page():
    """Serves the help page."""
    return render_template('help.html')
