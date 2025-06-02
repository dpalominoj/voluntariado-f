from flask_login import current_user
from model.models import Actividades # Assuming Actividades is your program model
from services.prediction_service import get_compatibility_scores # Assuming this is your service

def get_programs_compatibility():
    """
    Fetches programs (Actividades) based on user status and role,
    and calculates compatibility scores for authenticated volunteer users.
    """
    compatibility_scores = {}
    programs = []

    if current_user.is_anonymous:
        programs = Actividades.query.filter(Actividades.estado == 'abierto').all()
        # compatibility_scores remains {}

    elif current_user.is_authenticated:
        if current_user.perfil == 'voluntario':
            programs = Actividades.query.filter(Actividades.estado != 'cerrado').all()

            # Prepare user profile data
            user_disabilities = [udp.discapacidad.nombre for udp in current_user.discapacidades_pivot if udp.discapacidad and udp.discapacidad.nombre]
            user_interests = [pref.nombre_corto for pref in current_user.preferencias if pref.nombre_corto]

            user_profile_data = {
                'id': current_user.id_usuario,
                'username': current_user.nombre,
                'interests': user_interests, # Using actual user interests
                'skills': ['writing', 'gardening'], # Placeholder for skills
                'disabilities': user_disabilities # Using actual user disabilities
            }

            # Prepare program data for the service
            program_data_for_service = []
            for p in programs: # Use filtered programs
                program_data_for_service.append({
                    'id': p.id_actividad,
                    'name': p.nombre,
                    'description': p.descripcion,
                    # Use etiqueta or fallback to an empty string if nombre is None
                    'category': p.etiqueta if p.etiqueta else (p.nombre.lower() if p.nombre else "")
                })

            if program_data_for_service:
                try:
                    compatibility_scores = get_compatibility_scores(user_profile_data, program_data_for_service)
                except Exception as e:
                    # Log the exception or handle it as needed
                    print(f"Error calculating compatibility scores: {e}")
                    # compatibility_scores remains empty or you could set it to None or an error indicator
        else: # Authenticated but not a voluntario
            programs = Actividades.query.filter(Actividades.estado == 'abierto').all()
            # compatibility_scores remains {}
    # The 'else' case for when a user is neither anonymous nor authenticated should ideally not be reached
    # if Flask-Login is correctly configured, as current_user should always be one or the other.
    # However, to be safe, we can default to showing 'abierto' programs.
    else:
        programs = Actividades.query.filter(Actividades.estado == 'abierto').all()
        # compatibility_scores remains {}

    return programs, compatibility_scores
