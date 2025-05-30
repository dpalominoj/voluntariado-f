from flask import Blueprint, render_template
from flask_login import current_user # Import current_user
from model.models import Program, Activity # User might be needed later
from services.prediction_service import get_compatibility_scores # Import the service

main_bp = Blueprint('main', __name__, template_folder='../view/templates')

@main_bp.route('/')
def home():
    """Serves the home page."""
    return render_template('home.html')

@main_bp.route('/programs')
def programs():
    """Serves the page listing all programs."""
    all_programs = Program.query.all()
    compatibility_scores = {}

    if current_user.is_authenticated and current_user.role == 'Volunteer':
        # Create a dummy user profile for now - this would come from the User model or a more detailed profile
        user_profile_data = {
            'id': current_user.id,
            'username': current_user.username,
            'interests': ['environment', 'education', 'animals'], # Example interests
            'skills': ['writing', 'gardening'] # Example skills
        }
        
        # Prepare program data for the service
        program_data_for_service = [
            {'id': p.id, 'name': p.name, 'description': p.description, 'category': p.name.lower()} # Assuming name can act as category
            for p in all_programs
        ]
        
        if program_data_for_service:
            compatibility_scores = get_compatibility_scores(user_profile_data, program_data_for_service)

    return render_template('programs.html', programs=all_programs, compatibility_scores=compatibility_scores)

@main_bp.route('/help')
def help_page():
    """Serves the help page."""
    return render_template('help.html')
