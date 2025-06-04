from flask import Blueprint, render_template, request
from flask_login import current_user # Import current_user
from model.models import Usuarios, Organizaciones, Discapacidades, Actividades, EstadoActividad, Preferencias
from database.db import db
from controller.program_controller import get_programs_compatibility # Import the new function

main_bp = Blueprint('main', __name__, template_folder='../view/templates')

@main_bp.route('/')
def home():
    """Serves the home page."""
    return render_template('home.html')

@main_bp.route('/programs')
def programs():
    """Serves the page listing all programs, with filtering capabilities."""
    # Get filter values from request arguments
    tipo_filter = request.args.get('tipo', None)
    organizacion_filter = request.args.get('organizacion', None)
    estado_filter = request.args.get('estado', None)
    enfoque_inclusivo_filter = request.args.get('enfoque_inclusivo', None) # New filter

    # Fetch data for filter dropdowns
    tipos = [r[0] for r in db.session.query(Actividades.tipo).distinct().all() if r[0]] # Ensure not None
    organizaciones = Organizaciones.query.order_by(Organizaciones.nombre_org).all()
    discapacidades = Discapacidades.query.order_by(Discapacidades.nombre).all()
    estados = [e.value for e in EstadoActividad]
    preferencias_filter_options = Preferencias.query.order_by(Preferencias.nombre_corto).all()

    # Call get_programs_compatibility with filter values
    all_programs, compatibility_scores = get_programs_compatibility(
        tipo_filter=tipo_filter,
        organizacion_filter=organizacion_filter,
        estado_filter=estado_filter,
        enfoque_inclusivo=enfoque_inclusivo_filter, # Pass the new filter
        preferencia_filter=request.args.get('preferencia', None)
    )

    return render_template('programs.html',
                           programs=all_programs,
                           compatibility_scores=compatibility_scores,
                           tipos=tipos,
                           organizaciones=organizaciones,
                           discapacidades_filter_options=discapacidades, # Renamed to avoid clash
                           preferencias_filter_options=preferencias_filter_options,
                           estados=estados,
                           current_filters=request.args)

@main_bp.route('/help')
def help_page():
    """Serves the help page."""
    return render_template('help.html')
