from datetime import datetime, date, timezone, timedelta
from werkzeug.security import generate_password_hash

# Define peru_tz
peru_tz = timezone(timedelta(hours=-5))

# Dummy classes to allow the code to be syntactically valid if these are not defined elsewhere
class Organizacion:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    @staticmethod
    def query(*args, **kwargs): return type('Query', (), {'count': lambda: 0})()

class Discapacidad:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    @staticmethod
    def query(*args, **kwargs): return type('Query', (), {'count': lambda: 0})()

class Preferencia:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    @staticmethod
    def query(*args, **kwargs): return type('Query', (), {'count': lambda: 0})()

class ActividadFacilidad:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    @staticmethod
    def query(*args, **kwargs): return type('Query', (), {'count': lambda: 0})()

class Usuario:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    @staticmethod
    def query(*args, **kwargs): return type('Query', (), {'count': lambda: 0})()

class Actividad:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    @staticmethod
    def query(*args, **kwargs): return type('Query', (), {'count': lambda: 0})()

class UsuarioDiscapacidad:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class UsuarioPreferencia:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Dummy db.session object
class Session:
    def __init__(self):
        self.items = []
    def add(self, item):
        self.items.append(item)
    def add_all(self, items):
        self.items.extend(items)
    def commit(self):
        print("Mock db.session.commit() called")

db = type('DB', (), {'session': Session()})()


# Crea organizaciones
if Organizacion.query.count() == 0:
    organizaciones = [
        Organizacion(
            nombre_org="Fundación Inclusión Perú",
            descripcion_org="Organización dedicada a promover la inclusión social de personas con discapacidad",
            direccion_fisica="Av. Arequipa 123, Lima",
            logo="☺",
            fecha_registro=datetime(2025, 1, 13, 15, 0),
        ),
        Organizacion(
            nombre_org="Manos Solidarias",
            descripcion_org="ONG enfocada en brindar apoyo a comunidades vulnerables.",
            direccion_fisica="Calle Solidaridad 456, Cusco",
            logo="♥",
            fecha_registro=datetime(2024, 11, 20, 10, 30),
        ),
        Organizacion(
            nombre_org="Red de Voluntarios Ambientales",
            descripcion_org="Grupo dedicado a la conservación del medio ambiente y la educación ecológica.",
            direccion_fisica="Jr. Amazonas 789, Iquitos",
            logo="🌿",
            fecha_registro=datetime(2025, 2, 5, 9, 0),
        ),
         Organizacion(
            nombre_org="Corazones Unidos por la Infancia",
            descripcion_org="Asociación que trabaja por el bienestar y desarrollo de niños en situación de riesgo.",
            direccion_fisica="Av. Los Niños 321, Trujillo",
            logo="🧒",
            fecha_registro=datetime(2024, 10, 1, 14, 15),
        ),
    ]
    db.session.add_all(organizaciones)

# Crea discapacidades
if Discapacidad.query.count() == 0:
    discapacidades = [
        Discapacidad(nombre="Auditiva", descripcion="Dificultad o imposibilidad de usar el sentido del oído"),
        Discapacidad(nombre="Visual", descripcion="Dificultad o imposibilidad de usar el sentido de la vista"),
        Discapacidad(nombre="Motriz", descripcion="Dificultad o imposibilidad de moverse o desplazarse")
    ]
    db.session.add_all(discapacidades)

# Crea preferencias
if Preferencia.query.count() == 0:
    preferencias = [
        Preferencia(nombre_corto="Niños y Adolescentes", descripcion_detallada="Trabajar con niños y adolescentes"),
        Preferencia(nombre_corto="Educación y formación", descripcion_detallada="Actividades educativas"),
        Preferencia(nombre_corto="Ambiente y sostenibilidad", descripcion_detallada="Actividades ambientales"),
        Preferencia(nombre_corto="Deporte y recreación", descripcion_detallada="Actividades deportivas")
    ]
    db.session.add_all(preferencias)

# Crea facilidades para actividades
if ActividadFacilidad.query.count() == 0:
    actividadfacilidad = [
        ActividadFacilidad(nombre_facilidad="Rampas", descripcion="Acceso con rampas para sillas de ruedas"),
        ActividadFacilidad(nombre_facilidad="Intérpretes", descripcion="Intérpretes de lengua de señas disponibles"),
        ActividadFacilidad(nombre_facilidad="Material braille", descripcion="Material disponible en sistema braille"),
        ActividadFacilidad(nombre_facilidad="Materiales en audio", descripcion="Material accesible en audio"),
        ActividadFacilidad(nombre_facilidad="Otros", descripcion="Otros")
    ]
    db.session.add_all(actividadfacilidad)

# Crea usuarios
if Usuario.query.count() == 0:
    usuarios = [
        # Administrador
        Usuario(
            DNI="12345678",
            nombre="Dany",
            apellido="Palomino",
            email="admin@konectai.com",
            contrasena_hash=generate_password_hash("Hashed12"),
            celular="987654321",
            direccion="Av. Principal 123",
            fecha_nacimiento=date(1980, 5, 15),
            genero="masculino",
            perfil="administrador",
            tiene_discapacidad=False,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        ),
        # Organizador 1
        Usuario(
            DNI="87654321",
            nombre="Ana",
            apellido="García",
            email="ana.garcia@inclusionperu.org",
            contrasena_hash=generate_password_hash("Hashed23"),
            celular="912345678",
            direccion="Calle Secundaria 456",
            fecha_nacimiento=date(1992, 8, 20),
            genero="femenino",
            perfil="organizador",
            tiene_discapacidad=False,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=1
        ),
        # Organizador 2
        Usuario(
            DNI="11223344",
            nombre="Carlos",
            apellido="Lopez",
            email="carlos.lopez@manossolidarias.org",
            contrasena_hash=generate_password_hash("Hashed34"),
            celular="923456789",
            direccion="Av. Libertad 789",
            fecha_nacimiento=date(1985, 3, 10),
            genero="masculino",
            perfil="organizador",
            tiene_discapacidad=False,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=2
        ),
        # Voluntarios
        Usuario(
            DNI="44556677",
            nombre="Elena",
            apellido="Rojas",
            email="elena@email.com",
            contrasena_hash=generate_password_hash("Hashed44"),
            celular="987654334",
            direccion="Jr. Cusco 3031",
            fecha_nacimiento=date(1988, 4, 27),
            genero="femenino",
            perfil="voluntario",
            tiene_discapacidad=True,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        ),
        Usuario(
            DNI="55667788",
            nombre="Javier",
            apellido="Paredes",
            email="javier.paredes@example.com",
            contrasena_hash=generate_password_hash("Hashed55"),
            celular="998877665",
            direccion="Calle Los Pinos 450",
            fecha_nacimiento=date(1995, 11, 5),
            genero="masculino",
            perfil="voluntario",
            tiene_discapacidad=True,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        ),
        Usuario(
            DNI="66778899",
            nombre="Sofia",
            apellido="Castro",
            email="sofia.castro@example.com",
            contrasena_hash=generate_password_hash("Hashed66"),
            celular="911223344",
            direccion="Av. El Sol 987",
            fecha_nacimiento=date(2000, 7, 12),
            genero="femenino",
            perfil="voluntario",
            tiene_discapacidad=True,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        ),
        Usuario(
            DNI="77889900",
            nombre="Luis",
            apellido="Mendoza",
            email="luis.mendoza@example.com",
            contrasena_hash=generate_password_hash("Hashed77"),
            celular="933445566",
            direccion="Jr. Las Palmeras 123",
            fecha_nacimiento=date(1998, 1, 25),
            genero="masculino",
            perfil="voluntario",
            tiene_discapacidad=True,
            estado_usuario="pendiente",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        ),
        Usuario(
            DNI="88990011",
            nombre="Carmen",
            apellido="Diaz",
            email="carmen.diaz@example.com",
            contrasena_hash=generate_password_hash("Hashed88"),
            celular="944556677",
            direccion="Calle Las Begonias 789",
            fecha_nacimiento=date(1993, 9, 30),
            genero="femenino",
            perfil="voluntario",
            tiene_discapacidad=True,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        ),
        Usuario(
            DNI="99001122",
            nombre="Pedro",
            apellido="Vargas",
            email="pedro.vargas@example.com",
            contrasena_hash=generate_password_hash("Hashed99"),
            celular="955667788",
            direccion="Av. Los Incas 321",
            fecha_nacimiento=date(1996, 6, 18),
            genero="masculino",
            perfil="voluntario",
            tiene_discapacidad=True,
            estado_usuario="activo",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        ),
        Usuario(
            DNI="00112233",
            nombre="Rosa",
            apellido="Chavez",
            email="rosa.chavez@example.com",
            contrasena_hash=generate_password_hash("Hashed00"),
            celular="966778899",
            direccion="Jr. Union 654",
            fecha_nacimiento=date(1991, 12, 3),
            genero="femenino",
            perfil="voluntario",
            tiene_discapacidad=True,
            estado_usuario="bloqueado",
            fecha_registro=datetime.now(peru_tz),
            fk_organizacion=None
        )
    ]
    db.session.add_all(usuarios)

# Asignar discapacidades a los voluntarios
db.session.add(UsuarioDiscapacidad(id_usuario=4, id_discapacidad=1, gravedad="moderada", apoyo_requerido="interprete"))
db.session.add(UsuarioDiscapacidad(id_usuario=5, id_discapacidad=1, gravedad="leve", apoyo_requerido="otros"))
db.session.add(UsuarioDiscapacidad(id_usuario=6, id_discapacidad=1, gravedad="grave", apoyo_requerido="interprete"))
db.session.add(UsuarioDiscapacidad(id_usuario=7, id_discapacidad=2, gravedad="moderada", apoyo_requerido="otros"))
db.session.add(UsuarioDiscapacidad(id_usuario=8, id_discapacidad=2, gravedad="leve", apoyo_requerido="otros"))
db.session.add(UsuarioDiscapacidad(id_usuario=9, id_discapacidad=3, gravedad="grave", apoyo_requerido="otros"))
db.session.add(UsuarioDiscapacidad(id_usuario=10, id_discapacidad=3, gravedad="moderada", apoyo_requerido="otros"))

# Asignar preferencias a usuarios
db.session.add(UsuarioPreferencia(id_usuario=2, id_preferencia=1))
db.session.add(UsuarioPreferencia(id_usuario=2, id_preferencia=2))
db.session.add(UsuarioPreferencia(id_usuario=3, id_preferencia=3))
db.session.add(UsuarioPreferencia(id_usuario=3, id_preferencia=4))
db.session.add(UsuarioPreferencia(id_usuario=4, id_preferencia=1))
db.session.add(UsuarioPreferencia(id_usuario=4, id_preferencia=4))
db.session.add(UsuarioPreferencia(id_usuario=5, id_preferencia=2))
db.session.add(UsuarioPreferencia(id_usuario=6, id_preferencia=3))
db.session.add(UsuarioPreferencia(id_usuario=7, id_preferencia=1))
db.session.add(UsuarioPreferencia(id_usuario=8, id_preferencia=4))
db.session.add(UsuarioPreferencia(id_usuario=9, id_preferencia=4))
db.session.add(UsuarioPreferencia(id_usuario=10, id_preferencia=2))

# Crear actividades
if Actividad.query.count() == 0:
    actividades = [
        Actividad(
            nombre="Taller de lectura inclusiva",
            descripcion="Taller de lectura para personas con discapacidad visual",
            fecha_actividad=datetime(2025, 1, 15, 10, 0),
            ubicacion="Biblioteca Nacional, Lima",
            tipo="presencial",
            habilidades_requeridas="Paciencia, conocimiento básico de braille",
            es_inclusiva=True,
            cupo_maximo=20,
            estado="abierto",
            imagen="lectura_inclusiva.jpg",
            compatibilidad="95",
            etiqueta="educación",
            fk_organizacion=1,
            id_facilidad=3
        ),
        Actividad(
            nombre="Clases de lengua de señas",
            descripcion="Curso básico de lengua de señas peruana",
            fecha_actividad=datetime(2025, 2, 1, 18, 0),
            ubicacion="Online",
            tipo="virtual",
            habilidades_requeridas="Ninguna",
            es_inclusiva=True,
            cupo_maximo=30,
            estado="abierto",
            imagen="lengua_senas.jpg",
            compatibilidad="90",
            etiqueta="educación",
            fk_organizacion=1,
            id_facilidad=2
        ),
        Actividad(
            nombre="Campaña de reforestación en Lomas de Lúcumo",
            descripcion="Jornada de plantación de árboles nativos y limpieza de senderos.",
            fecha_actividad=datetime(2025, 3, 22, 9, 0),
            ubicacion="Lomas de Lúcumo, Pachacamac, Lima",
            tipo="presencial",
            habilidades_requeridas="Resistencia física básica, amor por la naturaleza.",
            es_inclusiva=False,
            cupo_maximo=50,
            estado="abierto",
            imagen="reforestacion_lomas.jpg",
            compatibilidad="75",
            etiqueta="ambiente y sostenibilidad",
            fk_organizacion=3,
            id_facilidad=1
        ),
        Actividad(
            nombre="Apoyo psicológico con señas a adolescentes",
            descripcion="Apoyo emocional a adolescentes en riesgo",
            fecha_actividad=datetime(2025, 3, 12, 10, 0),
            ubicacion="Huancayo, Perú",
            tipo="virtual",
            habilidades_requeridas="conocimiento de señas",
            es_inclusiva=True,
            cupo_maximo=26,
            estado="abierto",
            imagen="festival_deportivo.jpg",
            compatibilidad="87",
            etiqueta="niños y adolescentes",
            fk_organizacion=4,
            id_facilidad=2
        )
    ]
    db.session.add_all(actividades)

# Commit changes (mocked)
db.session.commit()

print("datos_iniciales.py ejecutado")
