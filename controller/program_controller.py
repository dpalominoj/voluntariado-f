from flask_login import current_user
from model.models import Actividades # Assuming Actividades is your program model
from services.prediction_service import get_compatibility_scores # Assuming this is your service

def get_programs_compatibility():
    """
    Fetches all programs (Actividades) and calculates compatibility scores
    for authenticated volunteer users.
    """
    all_programs = Actividades.query.all()
    compatibility_scores = {}

    if current_user.is_authenticated and current_user.perfil == 'voluntario':
        # Prepare user profile data (this might need adjustment based on your actual User model structure)
        user_profile_data = {
            'id': current_user.id_usuario,
            'username': current_user.nombre, # Assuming 'nombre' is the username field
            'interests': ['environment', 'education', 'animals'], # Example: replace with actual user interests if available
            'skills': ['writing', 'gardening'] # Example: replace with actual user skills if available
        }

        # Prepare program data for the service
        program_data_for_service = []
        for p in all_programs:
            program_data_for_service.append({
                'id': p.id_actividad,
                'name': p.nombre,
                'description': p.descripcion,
                'category': p.etiqueta if p.etiqueta else (p.nombre.lower() if p.nombre else "") # Use etiqueta or fallback
            })

        if program_data_for_service:
            try:
                compatibility_scores = get_compatibility_scores(user_profile_data, program_data_for_service)
            except Exception as e:
                # Log the exception or handle it as needed
                print(f"Error calculating compatibility scores: {e}")
                # compatibility_scores remains empty or you could set it to None or an error indicator

    return all_programs, compatibility_scores
