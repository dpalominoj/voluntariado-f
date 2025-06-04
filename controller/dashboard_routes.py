from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from model.models import UsuarioDiscapacidad, Discapacidades, Inscripciones, Actividades, Usuarios, EstadoActividad # Added EstadoActividad
from database.db import db # Added import
from services.participation_service import predecir_participacion # Path updated due to file rename
from services.compatibility_service import get_compatibility_scores # Import for compatibility service

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
        created_programs_query = []
        if organizer_org_ids:
            created_programs_query = Actividades.query.filter(Actividades.id_organizacion.in_(organizer_org_ids)) \
                                               .order_by(Actividades.fecha_actividad.desc()) \
                                               .all()

        actividades_con_prediccion = []
        for actividad in created_programs_query:
            prediction_output = predecir_participacion(actividad.id_actividad)

            prob = -1 # Default if no probability available
            indicator = '⚪'
            indicator_text = 'Predicción no disponible'

            if prediction_output and 'error' not in prediction_output and 'probabilidad' in prediction_output :
                prob = prediction_output['probabilidad']
                if prob is None: # Handles cases where predecir_participacion might return None for prob
                    indicator = '⚪'
                    indicator_text = 'Probabilidad no calculada (ej. datos insuficientes)'
                elif prob < 0.3:
                    indicator = '🔴'
                    indicator_text = f"Baja participación (Prob: {prob:.2f})"
                elif prob < 0.7:
                    indicator = '🟠'
                    indicator_text = f"Participación moderada (Prob: {prob:.2f})"
                else:
                    indicator = '🟢'
                    indicator_text = f"Alta participación (Prob: {prob:.2f})"
            elif prediction_output and 'error' in prediction_output:
                 indicator_text = prediction_output['error']
            elif prediction_output and 'info' in prediction_output: # Case for insufficient data without error
                indicator_text = prediction_output['info']


            actividades_con_prediccion.append({
                'actividad': actividad,
                'indicador': indicator,
                'texto_indicador': indicator_text,
                'metricas': prediction_output.get('metricas') if prediction_output else None,
                'tree_dot_file': prediction_output.get('tree_dot_file') if prediction_output else None
            })

        member_organizations = current_user.organizaciones

        # Removed Fetch Top Recommended Activities - part of the old system
        # print("Organizer dashboard: Fetching top recommended activities.")
        # recommended_activities = get_top_recommended_activities(limit=10)
        # print(f"Organizer Dashboard: Displaying {len(recommended_activities)} recommended activities.") # For logging

        return render_template('organizer_dashboard.html',
                               title="Organizer Dashboard",
                               created_programs_con_prediccion=actividades_con_prediccion, # Pass new list
                               member_organizations=member_organizations)
                               # recommended_activities=recommended_activities) # Removed
    elif current_user.perfil == 'voluntario':
        user_enrollments = db.session.query(Inscripciones, Actividades) \
                            .join(Actividades, Inscripciones.id_actividad == Actividades.id_actividad) \
                            .filter(Inscripciones.id_usuario == current_user.id_usuario) \
                            .order_by(Inscripciones.fecha_inscripcion.desc()) \
                            .all()

        actividades_abiertas = Actividades.query.filter_by(estado=EstadoActividad.ABIERTO).all()
        actividades_abiertas_con_prediccion = []

        # Prepare user profile for compatibility scoring
        user_disabilities = []
        if hasattr(current_user, 'discapacidades_pivot'):
            user_disabilities = [
                udp.discapacidad.nombre.value
                for udp in current_user.discapacidades_pivot
                if udp.discapacidad and udp.discapacidad.nombre
            ]

        user_profile = {
            'id': current_user.id_usuario,
            'username': current_user.nombre, # Added
            'interests': [p.nombre_corto for p in current_user.preferencias],
            'skills': ['writing', 'gardening'], # Added placeholder
            'disabilities': user_disabilities # Added
        }

        # Prepare activities for compatibility scoring
        programs_or_activities_for_compatibility = []
        for actividad in actividades_abiertas:
            item_data = {
                'id': actividad.id_actividad,
                'name': actividad.nombre,
                'description': actividad.descripcion if actividad.descripcion else '', # Added
                'category': actividad.etiqueta if actividad.etiqueta else (actividad.nombre.lower() if actividad.nombre else "") # Adjusted category logic
            }
            programs_or_activities_for_compatibility.append(item_data)

        compatibility_scores = {} # Default to empty dict
        if user_profile and programs_or_activities_for_compatibility: # Ensure inputs are not empty
            try:
                compatibility_scores = get_compatibility_scores(user_profile, programs_or_activities_for_compatibility)
            except Exception as e:
                print(f"Error calling get_compatibility_scores: {e}") # Log error
                flash("Error al calcular la compatibilidad de actividades.", "danger")
                # compatibility_scores will remain empty, so activities won't be filtered by it harshly

        for actividad in actividades_abiertas:
            prediction_output = predecir_participacion(actividad.id_actividad)

            prob = -1 # Default if no probability available
            indicator = '⚪'
            indicator_text = 'Predicción no disponible'

            if prediction_output and 'error' not in prediction_output and 'probabilidad' in prediction_output:
                prob = prediction_output['probabilidad']
                if prob is None:
                    indicator = '⚪'
                    indicator_text = 'Probabilidad no calculada (ej. datos insuficientes)'
                elif prob < 0.3:
                    indicator = '🔴'
                    indicator_text = f"Baja participación (Prob: {prob:.2f})"
                elif prob < 0.7:
                    indicator = '🟠'
                    indicator_text = f"Participación moderada (Prob: {prob:.2f})"
                else:
                    indicator = '🟢'
                    indicator_text = f"Alta participación (Prob: {prob:.2f})"
            elif prediction_output and 'error' in prediction_output:
                 indicator_text = prediction_output['error']
            elif prediction_output and 'info' in prediction_output: # Case for insufficient data without error
                indicator_text = prediction_output['info']

            # Get compatibility score, default to 0 if not found or error in service
            activity_score = 0
            if isinstance(compatibility_scores, dict): # Make sure it's a dict before using .get
                 activity_score_value = compatibility_scores.get(str(actividad.id_actividad)) # IDs might be strings from service
                 if activity_score_value is not None:
                     activity_score = activity_score_value

            actividades_abiertas_con_prediccion.append({
                'actividad': actividad,
                'indicador': indicator,
                'texto_indicador': indicator_text,
                'compatibility_score': activity_score
            })

        # Filter activities by compatibility score
        actividades_compatibles_filtradas = [
            actividad_info for actividad_info in actividades_abiertas_con_prediccion
            if actividad_info.get('compatibility_score', 0) > 50
        ]

        return render_template('volunteer_dashboard.html',
                               title="Volunteer Dashboard",
                               user_enrollments=user_enrollments,
                               actividades_compatibles=actividades_compatibles_filtradas) # Pass filtered list
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
        print(f"Organizer {current_user.id_usuario} manually triggered recommendation generation (currently disabled).")
        # Removed call to generate_user_based_recommendations as it's part of the old system.
        # generate_user_based_recommendations()
        flash("La generación manual de recomendaciones está actualmente deshabilitada.", "info")
        # print("Recommendation generation completed successfully after manual trigger.") # Old message
    except Exception as e:
        print(f"Error during (disabled) manually triggered recommendation generation: {e}")
        flash(f"Ocurrió un error: {str(e)}", "danger")
        # Log the full error e for debugging if necessary

    return redirect(url_for('user_dashboard.dashboard')) # Redirect back to the organizer dashboard
