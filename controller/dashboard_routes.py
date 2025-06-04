from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from model.models import UsuarioDiscapacidad, Discapacidades, Inscripciones, Actividades, Usuarios # Added imports
from database.db import db # Added import
from services.recommendation_service import generate_user_based_recommendations, get_top_recommended_activities

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
        total_users = Usuarios.query.count()
        total_programs = Actividades.query.count()
        return render_template('admin_dashboard.html', title="Admin Dashboard", total_users=total_users, total_programs=total_programs)
    elif current_user.perfil == 'organizador':
        organizer_org_ids = [org.id_organizacion for org in current_user.organizaciones]
        created_programs = []
        if organizer_org_ids:
            created_programs = Actividades.query.filter(Actividades.id_organizacion.in_(organizer_org_ids)) \
                                               .order_by(Actividades.fecha_actividad.desc()) \
                                               .all()
        member_organizations = current_user.organizaciones

        member_organizations = current_user.organizaciones

        # generate_user_based_recommendations() # REMOVED: This will be triggered manually by a button

        # Fetch Top Recommended Activities - this part remains
        print("Organizer dashboard: Fetching top recommended activities.")
        recommended_activities = get_top_recommended_activities(limit=10)

        print(f"Organizer Dashboard: Displaying {len(recommended_activities)} recommended activities.") # For logging

        return render_template('organizer_dashboard.html',
                               title="Organizer Dashboard",
                               created_programs=created_programs,
                               member_organizations=member_organizations,
                               recommended_activities=recommended_activities)
    elif current_user.perfil == 'voluntario':
        user_enrollments = db.session.query(Inscripciones, Actividades) \
                            .join(Actividades, Inscripciones.id_actividad == Actividades.id_actividad) \
                            .filter(Inscripciones.id_usuario == current_user.id_usuario) \
                            .order_by(Inscripciones.fecha_inscripcion.desc()) \
                            .all()
        return render_template('volunteer_dashboard.html', title="Volunteer Dashboard", user_enrollments=user_enrollments)
    else: # Should not happen with defined roles
        flash("Perfil de usuario no reconocido.", "warning")
        return redirect(url_for('main.home'))

@dashboard_bp.route('/profile') # This will be accessible at /dashboard/profile
@login_required
def profile():
    """
    Displays the user's profile page.
    """
    user_disabilities_data = []
    if current_user.is_authenticated and hasattr(current_user, 'discapacidades_pivot'):
        user_general_preferences = list(current_user.preferencias)  # Fetch general preferences
        for disc_assoc in current_user.discapacidades_pivot:
            user_disabilities_data.append({
                'nombre': disc_assoc.discapacidad.nombre.value if disc_assoc.discapacidad and disc_assoc.discapacidad.nombre else "No especificada",
                'gravedad': disc_assoc.gravedad if disc_assoc.gravedad else "No especificada",
                'preferencias': user_general_preferences  # Add this line
            })

    user_preferences = current_user.preferencias

    user_enrollments = []
    if current_user.perfil == 'voluntario':
        user_enrollments = db.session.query(Inscripciones, Actividades) \
                                .join(Actividades, Inscripciones.id_actividad == Actividades.id_actividad) \
                                .filter(Inscripciones.id_usuario == current_user.id_usuario) \
                                .order_by(Inscripciones.fecha_inscripcion.desc()) \
                                .all()

    return render_template('profile.html',
                           user=current_user,
                           user_disabilities_data=user_disabilities_data,
                           user_preferences=user_preferences,
                           user_enrollments=user_enrollments,
                           title="My Profile")

@dashboard_bp.route('/admin/manage_users')
@login_required
def admin_manage_users():
    if current_user.perfil != 'administrador':
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('user_dashboard.dashboard'))

    all_users = Usuarios.query.order_by(Usuarios.id_usuario).all()
    return render_template('admin_manage_users.html', users=all_users, title="Gestionar Usuarios")

@dashboard_bp.route('/organizer/trigger-recommendations', methods=['POST'])
@login_required
def trigger_organizer_recommendations():
    # Ensure the user is an organizer
    if current_user.perfil != 'organizador':
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('main.home')) # Or some other appropriate redirect

    try:
        print(f"Organizer {current_user.id_usuario} manually triggered recommendation generation.")
        # Call the function to generate recommendations for all relevant users
        generate_user_based_recommendations()
        flash("Se han actualizado las recomendaciones de actividades para los usuarios.", "success")
        print("Recommendation generation completed successfully after manual trigger.")
    except Exception as e:
        print(f"Error during manually triggered recommendation generation: {e}")
        flash(f"Ocurrió un error al generar las recomendaciones: {str(e)}", "danger") # Use str(e) for safer flashing
        # Log the full error e for debugging if necessary

    return redirect(url_for('user_dashboard.dashboard')) # Redirect back to the organizer dashboard
