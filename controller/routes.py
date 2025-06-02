from flask import Blueprint, render_template
from flask_login import current_user # Import current_user
from model.models import Usuarios # Updated imports - Actividades removed
# get_compatibility_scores removed
from controller.program_controller import get_programs_compatibility # Import the new function

main_bp = Blueprint('main', __name__, template_folder='../view/templates')

@main_bp.route('/')
def home():
    """Serves the home page."""
    return render_template('home.html')

@main_bp.route('/programs')
def programs():
    """Serves the page listing all programs."""
    all_programs, compatibility_scores = get_programs_compatibility()
    return render_template('programs.html', programs=all_programs, compatibility_scores=compatibility_scores)

@main_bp.route('/help')
def help_page():
    """Serves the help page."""
    return render_template('help.html')
