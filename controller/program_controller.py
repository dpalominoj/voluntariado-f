from flask_login import current_user
from model.models import Actividades # Make sure Usuarios is imported if needed for relationships
from services.prediction_service import get_compatibility_scores
from sqlalchemy.orm import aliased

def get_programs_compatibility():
    compatibility_scores = {}
    programs = []

    if current_user.is_anonymous:
        # Scenario 1: Anonymous user
        # Show all programs with estado != 'cerrado'
        programs = Actividades.query.filter(Actividades.estado != 'cerrado').all()
        # compatibility_scores remains {}

    elif current_user.is_authenticated:
        if current_user.perfil == 'voluntario':
            # Existing logic for volunteers: show programs with estado != 'cerrado' and calculate compatibility
            programs = Actividades.query.filter(Actividades.estado != 'cerrado').all()

            user_disabilities = [udp.discapacidad.nombre for udp in current_user.discapacidades_pivot if udp.discapacidad and udp.discapacidad.nombre]
            user_interests = [pref.nombre_corto for pref in current_user.preferencias if pref.nombre_corto]

            user_profile_data = {
                'id': current_user.id_usuario,
                'username': current_user.nombre,
                'interests': user_interests,
                'skills': ['writing', 'gardening'], # Placeholder for skills
                'disabilities': user_disabilities
            }

            program_data_for_service = []
            for p in programs:
                program_data_for_service.append({
                    'id': p.id_actividad,
                    'name': p.nombre,
                    'description': p.descripcion,
                    'category': p.etiqueta if p.etiqueta else (p.nombre.lower() if p.nombre else "")
                })

            if program_data_for_service:
                try:
                    compatibility_scores = get_compatibility_scores(user_profile_data, program_data_for_service)
                except Exception as e:
                    print(f"Error calculating compatibility scores: {e}")
                    # compatibility_scores remains empty

        elif current_user.perfil == 'organizador':
            # Scenario 2: Authenticated 'organizador'
            # Show programs linked to their organization(s) and estado != 'cerrado'

            # Get organization IDs for the current organizer
            organizer_org_ids = [org.id_organizacion for org in current_user.organizaciones]

            if organizer_org_ids:
                programs = Actividades.query.filter(
                    Actividades.id_organizacion.in_(organizer_org_ids),
                    Actividades.estado != 'cerrado'
                ).all()
            else:
                # Organizer not linked to any organization, show no programs
                programs = []
            # compatibility_scores remains {}

        elif current_user.perfil == 'administrador':
            # Authenticated 'administrador'
            # Show all programs with estado != 'cerrado'
            programs = Actividades.query.filter(Actividades.estado != 'cerrado').all()
            # compatibility_scores remains {}

        else: # Other authenticated users (if any future roles are added)
            # Default for other authenticated roles: show 'abierto' programs or all non-closed programs
            # For now, let's align with showing all non-closed programs as a general rule.
            programs = Actividades.query.filter(Actividades.estado != 'cerrado').all()
            # compatibility_scores remains {}

    else:
        # This case should ideally not be reached if Flask-Login is correctly configured.
        # Default to showing non-closed programs as a fallback.
        programs = Actividades.query.filter(Actividades.estado != 'cerrado').all()
        # compatibility_scores remains {}

    return programs, compatibility_scores
