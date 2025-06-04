from flask import flash, redirect, url_for
from flask_login import current_user, login_required
from model.models import Actividades, Discapacidades, Inscripciones, EstadoActividad, Preferencias, actividad_discapacidad_table # Make sure Usuarios is imported if needed for relationships
from services.prediction_service import get_compatibility_scores, generate_user_based_recommendations
from sqlalchemy.orm import aliased
from database.db import db

def get_programs_compatibility(tipo_filter=None, organizacion_filter=None, estado_filter=None, enfoque_inclusivo=None, preferencia_filter=None):
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

    # New logic for enfoque_inclusivo
    if enfoque_inclusivo and enfoque_inclusivo != '':
        # This means a specific disability name is selected for filtering.
        query = query.join(actividad_discapacidad_table, Actividades.id_actividad == actividad_discapacidad_table.c.actividad_id) \
                     .join(Discapacidades, actividad_discapacidad_table.c.discapacidad_id == Discapacidades.id_discapacidad) \
                     .filter(Discapacidades.nombre == enfoque_inclusivo)
        # Add the following line to ensure only Actividades entities are returned
        query = query.with_entities(Actividades)

    # New filter by Preferencia ID
    if preferencia_filter and preferencia_filter.isdigit(): # Check if it's a valid ID
        pref = Preferencias.query.get(int(preferencia_filter))
        if pref and pref.nombre_corto:
            query = query.filter(Actividades.etiqueta == pref.nombre_corto)

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

@program_bp.route('/<int:program_id>/enroll', methods=['POST'])
@login_required
def enroll_program(program_id):
    program = Actividades.query.get_or_404(program_id)

    # Validation: User profile
    if current_user.perfil != 'voluntario':
        flash("Solo los voluntarios pueden inscribirse.", "danger")
        return redirect(url_for('main.programs')) # Or specific program detail page

    # Validation: Program status
    if program.estado != EstadoActividad.ABIERTO:
        flash("Este programa no está abierto para inscripciones.", "danger")
        return redirect(url_for('program.view_program_detail', program_id=program_id))

    # Validation: Already enrolled
    existing_inscription = Inscripciones.query.filter_by(
        id_usuario=current_user.id_usuario,
        id_actividad=program_id
    ).first()
    if existing_inscription:
        flash("Ya estás inscrito en este programa.", "info")
        return redirect(url_for('program.view_program_detail', program_id=program_id))

    # Optional Validation: Program capacity (cupo_maximo)
    if program.cupo_maximo is not None: # Ensure cupo_maximo is set
        # Assuming 'inscripciones' is the backref from Actividades to Inscripciones
        if len(program.inscripciones) >= program.cupo_maximo:
            flash("El programa ha alcanzado su cupo máximo.", "danger")
            return redirect(url_for('program.view_program_detail', program_id=program_id))

    # All checks passed, create enrollment
    try:
        new_inscription = Inscripciones(
            id_usuario=current_user.id_usuario,
            id_actividad=program_id
        )
        db.session.add(new_inscription)
        db.session.commit()
        flash("¡Inscripción exitosa!", "success")

        # Add this line:
        try:
            print(f"Attempting to update recommendations for user {current_user.id_usuario} after enrollment.")
            generate_user_based_recommendations(target_user_id=current_user.id_usuario)
            print(f"Successfully triggered recommendation update for user {current_user.id_usuario}.")
        except Exception as e_rec:
            print(f"Error updating recommendations for user {current_user.id_usuario}: {e_rec}")
            # Optionally, flash a less critical message or just log,
            # as the main enrollment was successful.

    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar la inscripción: {str(e)}", "danger")
        # Log the exception e for server-side diagnostics if needed

    return redirect(url_for('program.view_program_detail', program_id=program_id))
