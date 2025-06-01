from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum as SQLAlchemyEnum, Boolean, DECIMAL, Table, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

usuario_organizacion_table = Table('usuario_organizacion', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id_usuario'), primary_key=True),
    Column('organizacion_id', Integer, ForeignKey('organizaciones.id_organizacion'), primary_key=True)
)

usuarios_preferencia_table = Table('usuarios_preferencia', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id_usuario'), primary_key=True),
    Column('preferencia_id', Integer, ForeignKey('preferencias.id_preferencia'), primary_key=True)
)

usuario_discapacidad_table = Table('usuario_discapacidad', Base.metadata,
    Column('usuario_id', Integer, ForeignKey('usuarios.id_usuario'), primary_key=True),
    Column('discapacidad_id', Integer, ForeignKey('discapacidades.id_discapacidad'), primary_key=True)
)

actividad_discapacidad_table = Table('actividad_discapacidad', Base.metadata,
    Column('actividad_id', Integer, ForeignKey('actividades.id_actividad'), primary_key=True),
    Column('discapacidad_id', Integer, ForeignKey('discapacidades.id_discapacidad'), primary_key=True)
)

actividad_facilidad_table = Table('actividad_facilidad', Base.metadata,
    Column('actividad_id', Integer, ForeignKey('actividades.id_actividad'), primary_key=True),
    Column('facilidad_id', Integer, ForeignKey('facilidades.id_facilidad'), primary_key=True)
)

class Usuarios(Base, UserMixin):
    __tablename__ = 'usuarios'
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre_usuario = Column(String(255), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    correo_electronico = Column(String(255), unique=True, nullable=False)
    nombre_completo = Column(String(255))
    foto_perfil = Column(Text)
    rol = Column(SQLAlchemyEnum('administrador', 'organizador', 'participante', name='rol_usuario_enum'), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activo = Column(Boolean, default=True)

    organizaciones = relationship("Organizaciones", secondary=usuario_organizacion_table, back_populates="usuarios")
    preferencias = relationship("Preferencias", secondary=usuarios_preferencia_table, back_populates="usuarios_con_preferencia")
    discapacidades_usuario = relationship("Discapacidades", secondary=usuario_discapacidad_table, back_populates="usuarios_con_discapacidad")
    inscripciones = relationship("Inscripciones", back_populates="usuario")
    notificaciones = relationship("Notificaciones", back_populates="usuario_destino_notificacion")
    feedback_emitido = relationship("Feedback", back_populates="usuario_emisor_feedback")
    recomendaciones_recibidas = relationship("Recomendaciones", foreign_keys='Recomendaciones.id_usuario_recomendado', back_populates="usuario_recomendado")
    auditoria_modificaciones = relationship("AuditoriaActividad", back_populates="usuario_que_modifica")
    interacciones_chatbot = relationship("InteraccionesChatbot", back_populates="usuario_interaccion_chatbot")

    def set_password(self, password):
        self.contrasena = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasena, password)

    def get_id(self):
        return str(self.id_usuario)

class Organizaciones(Base):
    __tablename__ = 'organizaciones'
    id_organizacion = Column(Integer, primary_key=True, autoincrement=True)
    nombre_organizacion = Column(String(255), unique=True, nullable=False)
    descripcion = Column(Text)
    direccion = Column(Text)
    telefono = Column(String(50))
    correo_electronico_contacto = Column(String(255))
    sitio_web = Column(String(255))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    usuarios = relationship("Usuarios", secondary=usuario_organizacion_table, back_populates="organizaciones")
    actividades_organizadas = relationship("Actividades", back_populates="organizacion_responsable")

class Preferencias(Base):
    __tablename__ = 'preferencias'
    id_preferencia = Column(Integer, primary_key=True, autoincrement=True)
    nombre_preferencia = Column(String(255), unique=True, nullable=False)
    descripcion = Column(Text)

    usuarios_con_preferencia = relationship("Usuarios", secondary=usuarios_preferencia_table, back_populates="preferencias")

class Discapacidades(Base):
    __tablename__ = 'discapacidades'
    id_discapacidad = Column(Integer, primary_key=True, autoincrement=True)
    nombre_discapacidad = Column(String(255), unique=True, nullable=False)
    descripcion = Column(Text)

    usuarios_con_discapacidad = relationship("Usuarios", secondary=usuario_discapacidad_table, back_populates="discapacidades_usuario")
    actividades_con_discapacidad_asociada = relationship("Actividades", secondary=actividad_discapacidad_table, back_populates="discapacidades_asociadas_actividad")

class Actividades(Base):
    __tablename__ = 'actividades'
    id_actividad = Column(Integer, primary_key=True, autoincrement=True)
    nombre_actividad = Column(String(255), nullable=False)
    descripcion = Column(Text)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime)
    lugar = Column(String(255))
    costo = Column(DECIMAL(10, 2), default=0.00)
    capacidad_maxima = Column(Integer)
    estado_actividad = Column(SQLAlchemyEnum('planificada', 'en_curso', 'finalizada', 'cancelada', name='estado_actividad_enum'), nullable=False, default='planificada')
    id_organizacion_responsable = Column(Integer, ForeignKey('organizaciones.id_organizacion'))
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organizacion_responsable = relationship("Organizaciones", back_populates="actividades_organizadas")
    discapacidades_asociadas_actividad = relationship("Discapacidades", secondary=actividad_discapacidad_table, back_populates="actividades_con_discapacidad_asociada")
    facilidades_disponibles = relationship("Facilidades", secondary=actividad_facilidad_table, back_populates="actividades_con_facilidad")
    auditoria_de_actividad = relationship("AuditoriaActividad", back_populates="actividad_auditada")
    inscripciones_actividad = relationship("Inscripciones", back_populates="actividad_inscrita")
    feedback_recibido = relationship("Feedback", back_populates="actividad_relacionada_feedback")
    recomendaciones_de_actividad = relationship("Recomendaciones", foreign_keys='Recomendaciones.id_actividad_recomendada', back_populates="actividad_recomendada_info")


class AuditoriaActividad(Base):
    __tablename__ = 'auditoria_actividad'
    id_auditoria = Column(Integer, primary_key=True, autoincrement=True)
    id_actividad = Column(Integer, ForeignKey('actividades.id_actividad'), nullable=False)
    id_usuario_modifico = Column(Integer, ForeignKey('usuarios.id_usuario'))
    campo_modificado = Column(String(255))
    valor_anterior = Column(Text)
    valor_nuevo = Column(Text)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow)

    actividad_auditada = relationship("Actividades", back_populates="auditoria_de_actividad")
    usuario_que_modifica = relationship("Usuarios", back_populates="auditoria_modificaciones")

class Facilidades(Base):
    __tablename__ = 'facilidades'
    id_facilidad = Column(Integer, primary_key=True, autoincrement=True)
    nombre_facilidad = Column(String(255), unique=True, nullable=False)
    descripcion = Column(Text)

    actividades_con_facilidad = relationship("Actividades", secondary=actividad_facilidad_table, back_populates="facilidades_disponibles")

class Inscripciones(Base):
    __tablename__ = 'inscripciones'
    id_inscripcion = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario_inscrito = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad_inscrita = Column(Integer, ForeignKey('actividades.id_actividad'), nullable=False)
    fecha_inscripcion = Column(DateTime, default=datetime.utcnow)
    estado_inscripcion = Column(SQLAlchemyEnum('confirmada', 'cancelada', 'lista_de_espera', name='estado_inscripcion_enum'), nullable=False, default='confirmada')

    usuario = relationship("Usuarios", back_populates="inscripciones")
    actividad_inscrita = relationship("Actividades", back_populates="inscripciones_actividad")

class Notificaciones(Base):
    __tablename__ = 'notificaciones'
    id_notificacion = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario_destino = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo_notificacion = Column(SQLAlchemyEnum('recordatorio', 'actualizacion', 'cancelacion', 'nuevo_mensaje', name='tipo_notificacion_enum'))
    leida = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario_destino_notificacion = relationship("Usuarios", back_populates="notificaciones")

class Feedback(Base):
    __tablename__ = 'feedback'
    id_feedback = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario_emisor = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad_relacionada = Column(Integer, ForeignKey('actividades.id_actividad'), nullable=True)
    calificacion = Column(Integer)
    comentario = Column(Text)
    fecha_feedback = Column(DateTime, default=datetime.utcnow)

    usuario_emisor_feedback = relationship("Usuarios", back_populates="feedback_emitido")
    actividad_relacionada_feedback = relationship("Actividades", back_populates="feedback_recibido")

class Recomendaciones(Base):
    __tablename__ = 'recomendaciones'
    id_recomendacion = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario_recomendado = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    id_actividad_recomendada = Column(Integer, ForeignKey('actividades.id_actividad'), nullable=False)
    motivo_recomendacion = Column(Text)
    fecha_recomendacion = Column(DateTime, default=datetime.utcnow)

    usuario_recomendado = relationship("Usuarios", foreign_keys=[id_usuario_recomendado], back_populates="recomendaciones_recibidas")
    actividad_recomendada_info = relationship("Actividades", foreign_keys=[id_actividad_recomendada], back_populates="recomendaciones_de_actividad")

class Tendencias(Base):
    __tablename__ = 'tendencias'
    id_tendencia = Column(Integer, primary_key=True, autoincrement=True)
    nombre_tendencia = Column(String(255), nullable=False)
    descripcion = Column(Text)
    popularidad = Column(Integer)
    fecha_identificacion = Column(DateTime, default=datetime.utcnow)

class InteraccionesChatbot(Base):
    __tablename__ = 'interacciones_chatbot'
    id_interaccion = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario_interaccion = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=True)
    mensaje_usuario = Column(Text)
    respuesta_chatbot = Column(Text)
    fecha_interaccion = Column(DateTime, default=datetime.utcnow)

    usuario_interaccion_chatbot = relationship("Usuarios", back_populates="interacciones_chatbot")
