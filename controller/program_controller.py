from flask import flash, redirect, url_for
from flask_login import current_user, login_required
from model.models import Actividades, Discapacidades, Inscripciones, EstadoActividad, Preferencias, actividad_discapacidad_table
from services.compatibility_service import get_compatibility_scores
from database.db import db

def get_programs_compatibility(tipo_filter=None, organizacion_filter=None, estado_filter=None, enfoque_inclusivo=None, preferencia_filter=None):
    compatibility_scores = {}
    query = Actividades.query

    apply_default_status_filter = True
    default_status_is_abierto = True

    if current_user.is_authenticated:
        if current_user.perfil == 'organizador':
            organizer_org_ids = [org.id_organizacion for org in current_user.organizaciones]
            if organizer_org_ids:
                query = query.filter(Actividades.id_organizacion.in_(organizer_org_ids))
                default_status_is_abierto = False
            else:
                query = query.filter(Actividades.id_actividad == -1) # No programs if not linked

    if tipo_filter:
        query = query.filter(Actividades.tipo == tipo_filter)

    if organizacion_filter:
        query = query.filter(Actividades.id_organizacion == organizacion_filter)

    if enfoque_inclusivo and enfoque_inclusivo != '':
        query = query.join(actividad_discapacidad_table, Actividades.id_actividad == actividad_discapacidad_table.c.actividad_id) \
                     .join(Discapacidades, actividad_discapacidad_table.c.discapacidad_id == Discapacidades.id_discapacidad) \
                     .filter(Discapacidades.nombre == enfoque_inclusivo)
        query = query.with_entities(Actividades)

    if preferencia_filter and preferencia_filter.isdigit():
        pref = Preferencias.query.get(int(preferencia_filter))
        if pref and pref.nombre_corto:
            query = query.filter(Actividades.etiqueta == pref.nombre_corto)

    if estado_filter:
        query = query.filter(Actividades.estado == estado_filter)
        apply_default_status_filter = False
    elif apply_default_status_filter:
        if default_status_is_abierto:
            query = query.filter(Actividades.estado == 'abierto')
        elif current_user.is_authenticated and current_user.perfil == 'organizador':
            query = query.filter(Actividades.estado != 'cerrado')
        else:
            query = query.filter(Actividades.estado == 'abierto')


    programs = query.all()

    if current_user.is_authenticated and current_user.perfil == 'voluntario' and programs:
        user_disabilities = [udp.discapacidad.nombre for udp in current_user.discapacidades_pivot if udp.discapacidad and udp.discapacidad.nombre]
        user_interests = [pref.nombre_corto for pref in current_user.preferencias if pref.nombre_corto]

        user_profile_data = {
            'id': current_user.id_usuario,
            'username': current_user.nombre,
            'interests': user_interests,
            'skills': ['writing', 'gardening'],
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

    if current_user.perfil != 'voluntario':
        flash("Solo los voluntarios pueden inscribirse.", "danger")
        return redirect(url_for('main.programs'))

    if program.estado != EstadoActividad.ABIERTO:
        flash("Este programa no está abierto para inscripciones.", "danger")
        return redirect(url_for('program.view_program_detail', program_id=program_id))

    existing_inscription = Inscripciones.query.filter_by(
        id_usuario=current_user.id_usuario,
        id_actividad=program_id
    ).first()
    if existing_inscription:
        flash("Ya estás inscrito en este programa.", "info")
        return redirect(url_for('program.view_program_detail', program_id=program_id))

    if program.cupo_maximo is not None:
        if len(program.inscripciones) >= program.cupo_maximo:
            flash("El programa ha alcanzado su cupo máximo.", "danger")
            return redirect(url_for('program.view_program_detail', program_id=program_id))

    try:
        new_inscription = Inscripciones(
            id_usuario=current_user.id_usuario,
            id_actividad=program_id
        )
        db.session.add(new_inscription)
        db.session.commit()
        flash("¡Inscripción exitosa!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar la inscripción: {str(e)}", "danger")

    return redirect(url_for('program.view_program_detail', program_id=program_id))
