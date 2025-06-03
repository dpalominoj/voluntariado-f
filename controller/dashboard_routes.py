from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('user_dashboard', __name__, 
                         template_folder='../view/templates/dashboards',
                         url_prefix='/dashboard') # All routes in this BP will be under /dashboard

@dashboard_bp.route('/') # This will be accessible at /dashboard/
@login_required
def dashboard():
    """
    Redirects user to the appropriate dashboard based on their role.
    """
    if current_user.perfil == 'administrador':
        return render_template('admin_dashboard.html', title="Admin Dashboard")
    elif current_user.perfil == 'organizador':
        return render_template('organizer_dashboard.html', title="Organizer Dashboard")
    else: # Default to Volunteer
        return render_template('volunteer_dashboard.html', title="Volunteer Dashboard")

@dashboard_bp.route('/profile') # This will be accessible at /dashboard/profile
@login_required
def profile():
    """
    Displays the user's profile page.
    """
    return render_template('profile.html', user=current_user, title="My Profile")
