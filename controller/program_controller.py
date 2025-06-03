from flask_login import current_user
from model.models import Actividades, Discapacidades # Make sure Usuarios is imported if needed for relationships
from services.prediction_service import get_compatibility_scores
from sqlalchemy.orm import aliased

def get_programs_compatibility(tipo_filter=None, organizacion_filter=None, discapacidad_filter=None, estado_filter=None, inclusiva_filter=None):
    compatibility_scores = {}
    query = Actividades.query

    # Role-based pre-filtering and default status determination
    apply_default_status_filter = True
    default_status_is_abierto = True # Default to 'abierto'

    if current_user.is_authenticated:
        if current_user.perfil == 'organizador':
            organizer_org_ids = [org.id_organizacion for org in current_user.organizaciones]
            if organizer_org_ids:
                query = query.filter(Actividades.id_organizacion.in_(organizer_org_ids))
                # For organizers, default is to show their programs not 'cerrado' unless estado_filter specifies otherwise
                default_status_is_abierto = False
            else:
                # Organizer not linked to any organization, show no programs by default
                # This will result in query.all() returning empty if no other filters are applied that broaden the scope.
                query = query.filter(Actividades.id_actividad == -1) # No programs if not linked

        # For 'administrador', 'voluntario', or other authenticated users,
        # the default is 'abierto' unless overridden by estado_filter.
        # No specific pre-filters here beyond what filters below will handle.

    # Apply provided filters
    if tipo_filter:
        query = query.filter(Actividades.tipo == tipo_filter)

    if organizacion_filter: # This could override/narrow the organizer's own orgs if they use the filter
        query = query.filter(Actividades.id_organizacion == organizacion_filter)

    if discapacidad_filter:
        query = query.join(Actividades.discapacidades).filter(Discapacidades.id_discapacidad == discapacidad_filter)

    if inclusiva_filter is not None and inclusiva_filter != '':
        # Assuming inclusiva_filter is 'true' or 'false' as a string
        es_inclusiva_bool = inclusiva_filter.lower() == 'true'
        query = query.filter(Actividades.es_inclusiva == es_inclusiva_bool)

    # Status filter logic
    if estado_filter:
        query = query.filter(Actividades.estado == estado_filter)
        apply_default_status_filter = False # User specified a status, so don't apply default
    elif apply_default_status_filter:
        if default_status_is_abierto:
             # Anonymous users, volunteers, admins (by default), other authenticated users
            query = query.filter(Actividades.estado == 'abierto')
        elif current_user.is_authenticated and current_user.perfil == 'organizador':
            # Organizers viewing their own programs, default to not 'cerrado'
            query = query.filter(Actividades.estado != 'cerrado')
        else:
            # Fallback for anonymous or if something went wrong with role logic for status
            query = query.filter(Actividades.estado == 'abierto')


    programs = query.all()

    # Compatibility scores calculation (only for volunteers and if programs are found)
    if current_user.is_authenticated and current_user.perfil == 'voluntario' and programs:
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

    return programs, compatibility_scores

from flask import Blueprint, render_template, redirect, url_for, flash

program_bp = Blueprint('program', __name__,
                           template_folder='../view/templates',
                           url_prefix='/program')

@program_bp.route('/<int:program_id>')
def view_program_detail(program_id):
    program = Actividades.query.get(program_id)
    if not program:
        flash('Programa no encontrado.', 'danger')
        return redirect(url_for('main.programs'))
    return render_template('program_detail.html', program=program, title=program.nombre)
