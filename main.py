from flask_login import UserMixin
from database.db import db  # Asegúrate que esto inicializa SQLAlchemy correctamente
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

# --- Tablas de asociación (usando db de Flask-SQLAlchemy) ---
usuario_organizacion_table = db.Table('usuario_organizacion', db.metadata,
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id_usuario'), primary_key=True),
    db.Column('organizacion_id', db.Integer, db.ForeignKey('organizaciones.id_organizacion'), primary_key=True)
)

usuarios_preferencia_table = db.Table('usuarios_preferencia', db.metadata,
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id_usuario'), primary_key=True),
    db.Column('preferencia_id', db.Integer, db.ForeignKey('preferencias.id_preferencia'), primary_key=True)
)

actividad_discapacidad_table = db.Table('actividad_discapacidad', db.metadata,
    db.Column('actividad_id', db.Integer, db.ForeignKey('actividades.id_actividad'), primary_key=True),
    db.Column('discapacidad_id', db.Integer, db.ForeignKey('discapacidades.id_discapacidad'), primary_key=True)
)

actividad_facilidad_table = db.Table('actividad_facilidad', db.metadata,
    db.Column('actividad_id', db.Integer, db.ForeignKey('actividades.id_actividad'), primary_key=True),
    db.Column('facilidad_id', db.Integer, db.ForeignKey('facilidad.id_facilidad'), primary_key=True)
)

# --- Definición de Enums ---
class TipoDiscapacidad(enum.Enum):
    AUDITIVA = "Auditiva"
    VISUAL = "Visual"
    MOTRIZ = "Motriz"

class EstadoActividad(enum.Enum):
    ABIERTO = "abierto"
    CERRADO = "cerrado"
    CANCELADA = "cancelada"
    FINALIZADA = "finalizada"

class EstadoUsuario(enum.Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    SUSPENDIDO = "suspendido"
    BLOQUEADO = "bloqueado"

class TipoRecomendacion(enum.Enum):
    PERSONALIZADA = "P"
    GRUPAL = "G"
    BUENAS_PRACTICAS = "BP"

# --- Modelos ---
class Usuarios(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Campos obligatorios
    DNI = db.Column(db.String(8), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    contrasena_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.Enum('voluntario', 'organizador', 'administrador', name='perfil_enum'), nullable=False)
    estado_usuario = db.Column(db.Enum(EstadoUsuario, name='estado_usuario_enum'), nullable=False, default=EstadoUsuario.ACTIVO)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Campos opcionales
    apellido = db.Column(db.String(100), nullable=True)
    celular = db.Column(db.String(9), unique=True, nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=True)
    direccion = db.Column(db.String(255), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    genero = db.Column(db.Enum('masculino', 'femenino', name='genero_enum'))

    # Relaciones
    organizaciones = db.relationship("Organizaciones", secondary=usuario_organizacion_table, back_populates="usuarios")
    preferencias = db.relationship("Preferencias", secondary=usuarios_preferencia_table, back_populates="usuarios")
    discapacidades_pivot = db.relationship("UsuarioDiscapacidad", back_populates="usuario", cascade="all, delete-orphan")
    inscripciones = db.relationship("Inscripciones", back_populates="usuario")
    notificaciones = db.relationship("Notificaciones", back_populates="usuario")
    feedback = db.relationship("Feedback", back_populates="usuario")
    recomendaciones = db.relationship("Recomendaciones", back_populates="usuario")
    interacciones_chatbot = db.relationship("InteraccionesChatbot", back_populates="usuario")

    def set_password(self, password):
        self.contrasena_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasena_hash, password)

    def get_id(self):
        return str(self.id_usuario)

class Organizaciones(db.Model):
    __tablename__ = 'organizaciones'
    id_organizacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_org = db.Column(db.String(255), unique=True, nullable=False)
    descripcion_org = db.Column(db.Text)
    direccion_fisica = db.Column(db.String(255))
    logo = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones
    usuarios = db.relationship("Usuarios", secondary=usuario_organizacion_table, back_populates="organizaciones")
    actividades = db.relationship("Actividades", back_populates="organizacion")

class Preferencias(db.Model):
    __tablename__ = 'preferencias'
    id_preferencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_corto = db.Column(db.String(50), unique=True)
    descripcion_detallada = db.Column(db.Text)

    usuarios = db.relationship("Usuarios", secondary=usuarios_preferencia_table, back_populates="preferencias")

class UsuarioDiscapacidad(db.Model):
    __tablename__ = 'usuario_discapacidad'
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), primary_key=True)
    id_discapacidad = db.Column(db.Integer, db.ForeignKey('discapacidades.id_discapacidad'), primary_key=True)
    gravedad = db.Column(db.Enum('leve', 'moderada', 'grave', name='gravedad_enum'))
    apoyo_requerido = db.Column(db.Enum('interprete', 'otros', name='apoyo_requerido_enum'))

    usuario = db.relationship("Usuarios", back_populates="discapacidades_pivot")
    discapacidad = db.relationship("Discapacidades", back_populates="usuarios_pivot")

class Discapacidades(db.Model):
    __tablename__ = 'discapacidades'
    id_discapacidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.Enum(TipoDiscapacidad), unique=True)
    descripcion = db.Column(db.Text)

    usuarios_pivot = db.relationship("UsuarioDiscapacidad", back_populates="discapacidad", cascade="all, delete-orphan")
    actividades = db.relationship("Actividades", secondary=actividad_discapacidad_table, back_populates="discapacidades")

class Actividades(db.Model):
    __tablename__ = 'actividades'
    id_actividad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(255))
    descripcion = db.Column(db.Text)
    fecha_actividad = db.Column(db.DateTime)
    ubicacion = db.Column(db.String(255))
    tipo = db.Column(db.Enum('presencial', 'virtual', name='tipo_actividad_enum'))
    habilidades_requeridas = db.Column(db.Text)
    es_inclusiva = db.Column(db.Boolean, default=False)
    cupo_maximo = db.Column(db.Integer)
    estado = db.Column(db.Enum(EstadoActividad, name='estado_actividad_enum'), default=EstadoActividad.ABIERTO)
    imagen = db.Column(db.String(255))
    compatibilidad = db.Column(db.Numeric(5, 2))  # Corregido a Numeric
    etiqueta = db.Column(db.String(100))
    id_organizacion = db.Column(db.Integer, db.ForeignKey('organizaciones.id_organizacion'))

    # Relaciones
    organizacion = db.relationship("Organizaciones", back_populates="actividades")
    discapacidades = db.relationship("Discapacidades", secondary=actividad_discapacidad_table, back_populates="actividades")
    facilidades = db.relationship("Facilidad", secondary=actividad_facilidad_table, back_populates="actividades")
    auditoria_actividad = db.relationship("AuditoriaActividad", back_populates="actividad")
    inscripciones = db.relationship("Inscripciones", back_populates="actividad")

class AuditoriaActividad(db.Model):
    __tablename__ = 'auditoria_actividad'
    id_auditoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    IP_usuario = db.Column(db.String(45))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    actividad = db.relationship("Actividades", back_populates="auditoria_actividad")
    usuario = db.relationship("Usuarios")

class Facilidad(db.Model):
    __tablename__ = 'facilidad'
    id_facilidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_facilidad = db.Column(db.String(255), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))

    actividades = db.relationship("Actividades", secondary=actividad_facilidad_table, back_populates="facilidades")

class Inscripciones(db.Model):
    __tablename__ = 'inscripciones'
    id_inscripcion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuarios", back_populates="inscripciones")
    actividad = db.relationship("Actividades", back_populates="inscripciones")

class Notificaciones(db.Model):
    __tablename__ = 'notificaciones'
    id_notificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    leida = db.Column(db.Boolean, default=False)
    prioridad = db.Column(db.Enum('alta', 'media', 'baja', name='prioridad_enum'))

    usuario = db.relationship("Usuarios", back_populates="notificaciones")

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id_feedback = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'))
    puntuacion = db.Column(db.Integer)
    comentario = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuarios", back_populates="feedback")
    actividad = db.relationship("Actividades")

class Recomendaciones(db.Model):
    __tablename__ = 'recomendaciones'
    id_recomendacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=False)
    tipo_recomendacion = db.Column(db.Enum(TipoRecomendacion, name='tipo_recomendacion_enum'))
    descripcion = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuarios", back_populates="recomendaciones")
    actividad = db.relationship("Actividades")

class Tendencias(db.Model):
    __tablename__ = 'tendencias'
    id_tendencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'))
    cantidad_participantes = db.Column(db.Integer)
    puntuacion_promedio = db.Column(db.Numeric(3, 2))  # Corregido a Numeric
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class InteraccionesChatbot(db.Model):
    __tablename__ = 'interacciones_chatbot'
    id_interaccion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    mensaje_usuario = db.Column(db.Text)
    respuesta_chatbot = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuarios", back_populates="interacciones_chatbot")
