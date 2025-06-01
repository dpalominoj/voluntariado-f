from flask_login import UserMixin
from database.db import db # Import db
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, Boolean, DECIMAL, Table, func

from sqlalchemy.orm import relationship

# from sqlalchemy.ext.declarative import declarative_base # Removed unused import
from datetime import datetime

# Base = declarative_base() # Removed

# Association table for Usuarios and Organizaciones (many-to-many)
usuario_organizacion_table = Table('usuario_organizacion', db.Model.metadata, # Changed Base.metadata to db.Model.metadata
    Column('usuario_id', Integer, ForeignKey('usuarios.id_usuario'), primary_key=True),
    Column('organizacion_id', Integer, ForeignKey('organizaciones.id_organizacion'), primary_key=True)
)

# Association table for Usuarios and Preferencias (many-to-many)
usuarios_preferencia_table = Table('usuarios_preferencia', db.Model.metadata, # Changed Base.metadata to db.Model.metadata
    Column('usuario_id', Integer, ForeignKey('usuarios.id_usuario'), primary_key=True),
    Column('preferencia_id', Integer, ForeignKey('preferencias.id_preferencia'), primary_key=True)
)

# Removed old usuario_discapacidad_table

# Association table for Actividades and Discapacidades (many-to-many)
actividad_discapacidad_table = Table('actividad_discapacidad', db.Model.metadata, # Changed Base.metadata to db.Model.metadata
    Column('actividad_id', Integer, ForeignKey('actividades.id_actividad'), primary_key=True),
    Column('discapacidad_id', Integer, ForeignKey('discapacidades.id_discapacidad'), primary_key=True)
)

# Association table for Actividades and Facilidades (many-to-many)
actividad_facilidad_table = Table('actividad_facilidad', db.Model.metadata,
    Column('actividad_id', Integer, ForeignKey('actividades.id_actividad'), primary_key=True),
    Column('facilidad_id', Integer, ForeignKey('facilidad.id_facilidad'), primary_key=True) # Updated FK to 'facilidad.id_facilidad'
)


class Usuarios(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DNI = db.Column(db.String(8), unique=True, nullable=True)
    nombre = db.Column(db.String(100)) # Changed from nombre_usuario, removed nombre_completo
    apellido = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False) # Changed from correo_electronico
    contrasena_hash = db.Column(db.String(255), nullable=False) # Changed from contrasena
    celular = db.Column(db.String(9), nullable=True)
    direccion = db.Column(db.Text, nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    genero = db.Column(db.Enum('masculino', 'femenino', name='genero_enum'), nullable=True)
    perfil = db.Column(db.Enum('voluntario', 'organizador', 'administrador', name='perfil_enum'), nullable=False) # Changed from rol
    estado_usuario = db.Column(db.Enum('activo', 'inactivo', name='estado_usuario_enum'), nullable=True, default='activo')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    # Removed: nombre_usuario, correo_electronico, nombre_completo, foto_perfil, rol, fecha_creacion, ultima_actualizacion, activo

    organizaciones = relationship("Organizaciones", secondary=usuario_organizacion_table, back_populates="usuarios")
    preferencias = relationship("Preferencias", secondary=usuarios_preferencia_table, back_populates="usuarios")
    # Old discapacidades relationship removed, new one 'discapacidades_pivot' will be added
    inscripciones = relationship("Inscripciones", back_populates="usuario")
    notificaciones = relationship("Notificaciones", back_populates="usuario")
    feedback = relationship("Feedback", back_populates="usuario")
    recomendaciones = relationship("Recomendaciones", back_populates="usuario")
    interacciones_chatbot = relationship("InteraccionesChatbot", back_populates="usuario")
    discapacidades_pivot = db.relationship("UsuarioDiscapacidad", back_populates="usuario", cascade="all, delete-orphan") # New relationship

    def set_password(self, password):
        self.contrasena_hash = generate_password_hash(password) # Updated to contrasena_hash

    def check_password(self, password):
        return check_password_hash(self.contrasena_hash, password) # Updated to contrasena_hash

    def get_id(self):
        return str(self.id_usuario)


class Organizaciones(db.Model):
    __tablename__ = 'organizaciones'
    id_organizacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_org = db.Column(db.String(255), unique=True, nullable=False) # Renamed from nombre_organizacion
    descripcion_org = db.Column(db.Text, nullable=True) # Renamed from descripcion
    direccion_fisica = db.Column(db.String(255), nullable=True) # Renamed from direccion
    logo = db.Column(db.Text, nullable=True) # Added logo
    fecha_registro = db.Column(db.DateTime, nullable=True) # Renamed from fecha_creacion, made nullable
    # Removed: telefono, correo_electronico_contacto, sitio_web, ultima_actualizacion

    usuarios = relationship("Usuarios", secondary=usuario_organizacion_table, back_populates="organizaciones")
    actividades = relationship("Actividades", back_populates="organizacion")


class Preferencias(db.Model):
    __tablename__ = 'preferencias'
    id_preferencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_corto = db.Column(db.String(50), unique=True, nullable=True) # Renamed from nombre_preferencia
    descripcion_detallada = db.Column(db.Text, nullable=True) # Renamed from descripcion

    usuarios = relationship("Usuarios", secondary=usuarios_preferencia_table, back_populates="preferencias")


# Nueva clase de asociacion UsuarioDiscapacidad
class UsuarioDiscapacidad(db.Model):
    __tablename__ = 'usuario_discapacidad'
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), primary_key=True)
    id_discapacidad = db.Column(db.Integer, db.ForeignKey('discapacidades.id_discapacidad'), primary_key=True)
    gravedad = db.Column(db.Enum('leve', 'moderada', 'grave', name='gravedad_enum'), nullable=True)
    apoyo_requerido = db.Column(db.Enum('interprete', 'otros', name='apoyo_requerido_enum'), nullable=True)

    usuario = db.relationship("Usuarios", back_populates="discapacidades_pivot")
    discapacidad = db.relationship("Discapacidades", back_populates="usuarios_pivot")


class Discapacidades(db.Model):
    __tablename__ = 'discapacidades'
    id_discapacidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), unique=True, nullable=True) # Renamed from nombre_discapacidad
    descripcion = db.Column(db.Text, nullable=True) # Kept as is, but ensured db.Column

    usuarios_pivot = db.relationship("UsuarioDiscapacidad", back_populates="discapacidad", cascade="all, delete-orphan") # Relationship verified
    actividades = relationship("Actividades", secondary=actividad_discapacidad_table, back_populates="discapacidades") # Updated back_populates


class Actividades(db.Model):
    __tablename__ = 'actividades'
    id_actividad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(255), nullable=True) # Renamed from nombre_actividad, made nullable
    descripcion = db.Column(db.Text, nullable=True) # Ensured db.Column
    fecha_actividad = db.Column(db.DateTime, nullable=True) # Renamed from fecha_inicio, made nullable
    ubicacion = db.Column(db.String(255), nullable=True) # Renamed from lugar
    tipo = db.Column(db.Enum('presencial', 'virtual', name='tipo_actividad_enum'), nullable=True) # Added tipo
    habilidades_requeridas = db.Column(db.Text, nullable=True) # Added habilidades_requeridas
    es_inclusiva = db.Column(db.Boolean, default=False, nullable=True) # Added es_inclusiva
    cupo_maximo = db.Column(db.Integer, nullable=True) # Renamed from capacidad_maxima
    estado = db.Column(db.Enum('abierto', 'cerrado', name='estado_actividad_enum_new'), nullable=True) # Renamed from estado_actividad, new enum
    imagen = db.Column(db.String(255), nullable=True) # Added imagen
    compatibilidad = db.Column(db.DECIMAL(5, 2), nullable=True) # Added compatibilidad
    etiqueta = db.Column(db.String(100), nullable=True) # Added etiqueta
    id_organizacion = db.Column(db.Integer, db.ForeignKey('organizaciones.id_organizacion'), nullable=True) # Made nullable
    # Removed: fecha_fin, costo, fecha_creacion, ultima_actualizacion

    organizacion = relationship("Organizaciones", back_populates="actividades")
    discapacidades = relationship("Discapacidades", secondary=actividad_discapacidad_table, back_populates="actividades") # Renamed from discapacidades_asociadas
    facilidades = relationship("Facilidad", secondary=actividad_facilidad_table, back_populates="actividades") # Renamed from facilidades_asociadas, changed target to Facilidad
    # auditoria_actividad relationship was already here, ensuring it stays
    auditoria_actividad = relationship("AuditoriaActividad", back_populates="actividad")
    inscripciones = relationship("Inscripciones", back_populates="actividad")


class AuditoriaActividad(db.Model):
    __tablename__ = 'auditoria_actividad'
    id_auditoria = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True) # Added id_usuario FK
    IP_usuario = db.Column(db.String(45), nullable=True) # Added IP_usuario
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow) # Renamed from fecha_modificacion
    # Removed: usuario_modificacion, campo_modificado, valor_anterior, valor_nuevo

    actividad = relationship("Actividades", back_populates="auditoria_actividad")
    usuario = relationship("Usuarios") # Kept simple as per instruction for now


class Facilidad(db.Model): # Renamed from Facilidades
    __tablename__ = 'facilidad' # Renamed table
    id_facilidad = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_facilidad = db.Column(db.String(255), unique=True, nullable=False) # Ensured db.Column
    descripcion = db.Column(db.String(255), nullable=True) # Changed type to String(255)

    actividades = relationship("Actividades", secondary=actividad_facilidad_table, back_populates="facilidades") # Updated back_populates


class Inscripciones(db.Model):
    __tablename__ = 'inscripciones'
    id_inscripcion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
    # Removed: estado_inscripcion

    usuario = relationship("Usuarios", back_populates="inscripciones")
    actividad = relationship("Actividades", back_populates="inscripciones")


class Notificaciones(db.Model):
    __tablename__ = 'notificaciones'
    id_notificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow) # Renamed from fecha_creacion
    leida = db.Column(db.Boolean, default=False)
    prioridad = db.Column(db.Enum('alta', 'media', 'baja', name='prioridad_enum'), nullable=True) # Added prioridad
    # Removed: tipo_notificacion

    usuario = relationship("Usuarios", back_populates="notificaciones")


class Feedback(db.Model):
    __tablename__ = 'feedback'
    id_feedback = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=True) # Ensured nullable
    puntuacion = db.Column(db.Integer, nullable=True) # Renamed from calificacion
    comentario = db.Column(db.Text, nullable=True) # Ensured nullable
    fecha = db.Column(db.DateTime, default=datetime.utcnow) # Renamed from fecha_feedback

    usuario = relationship("Usuarios", back_populates="feedback")
    actividad = relationship("Actividades") # Define relationship to Actividades if needed


class Recomendaciones(db.Model):
    __tablename__ = 'recomendaciones'
    id_recomendacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=False) # Renamed from id_actividad_recomendada
    tipo_recomendacion = db.Column(db.Enum('P', 'G', 'BP', name='tipo_recomendacion_enum'), nullable=True) # Added tipo_recomendacion
    descripcion = db.Column(db.Text, nullable=True) # Renamed from motivo_recomendacion
    fecha = db.Column(db.DateTime, default=datetime.utcnow) # Renamed from fecha_recomendacion

    usuario = relationship("Usuarios", back_populates="recomendaciones")
    actividad = relationship("Actividades") # Renamed from actividad_recomendada


class Tendencias(db.Model):
    __tablename__ = 'tendencias'
    id_tendencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_actividad = db.Column(db.Integer, db.ForeignKey('actividades.id_actividad'), nullable=True) # Added id_actividad FK
    cantidad_participantes = db.Column(db.Integer, nullable=True) # Added cantidad_participantes
    puntuacion_promedio = db.Column(db.DECIMAL(3,2), nullable=True) # Added puntuacion_promedio
    fecha = db.Column(db.DateTime, default=datetime.utcnow) # Renamed from fecha_identificacion
    # Removed: nombre_tendencia, descripcion, popularidad
    # Relationship to Actividades can be added if needed:
    # actividad = db.relationship("Actividades")


class InteraccionesChatbot(db.Model):
    __tablename__ = 'interacciones_chatbot'
    id_interaccion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=True) # Ensured nullable
    mensaje_usuario = db.Column(db.Text, nullable=True) # Ensured nullable
    respuesta_chatbot = db.Column(db.Text, nullable=True) # Ensured nullable
    fecha = db.Column(db.DateTime, default=datetime.utcnow) # Renamed from fecha_interaccion

    usuario = relationship("Usuarios", back_populates="interacciones_chatbot")
