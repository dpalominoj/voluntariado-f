import pytest
from services.compatibility_service import get_compatibility_scores
from flask import Flask # Import Flask to create an app context

# Crear una instancia de aplicación Flask para el contexto de la aplicación
# Esto es necesario porque compatibility_service.py usa current_app.logger
# y current_app requiere un contexto de aplicación activo.
@pytest.fixture(scope="module")
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    # Puedes añadir más configuraciones si son necesarias para tus servicios
    with app.app_context():
        yield app

def test_basic_scenario(app):
    """
    Prueba el cálculo de puntajes de compatibilidad para un escenario básico.
    Verifica que se devuelva un diccionario, las claves coincidan y los puntajes estén en rango.
    """
    user_profile = {
        'id': 1,
        'interests': ['medio ambiente', 'tecnología'],
        'skills': ['python', 'análisis de datos'],
        'disabilities': []
    }
    programs_or_activities = [
        {
            'id': 101,
            'name': 'Taller de Python para Ecologistas',
            'description': 'Aprende Python para analizar datos ambientales.',
            'category': 'tecnología',
            'es_inclusiva': False,
            'discapacidades_soportadas': []
        },
        {
            'id': 102,
            'name': 'Limpieza de Playa',
            'description': 'Participa en la limpieza de la playa local.',
            'category': 'medio ambiente',
            'es_inclusiva': False,
            'discapacidades_soportadas': []
        }
    ]

    scores = get_compatibility_scores(user_profile, programs_or_activities)

    assert isinstance(scores, dict), "La función debe devolver un diccionario."
    assert len(scores) == len(programs_or_activities), "El número de puntajes debe coincidir con el número de programas."

    for program in programs_or_activities:
        program_id = program['id']
        assert program_id in scores, f"El ID del programa {program_id} debe estar en los puntajes."
        score = scores[program_id]
        assert 0 <= score <= 100, f"El puntaje para el programa {program_id} ({score}) debe estar entre 0 y 100."

    # Verificación adicional: El programa más relevante debería tener un puntaje más alto.
    # (Esto es una expectativa, el modelo exacto podría variar pero es una buena heurística para este caso)
    if 101 in scores and 102 in scores:
        # El programa 101 combina 'tecnología' y 'medio ambiente' (por descripción)
        # El programa 102 es solo 'medio ambiente'
        # El usuario tiene intereses en ambos.
        # Es razonable esperar que 101 sea igual o más compatible.
        # Dado que el servicio considera 'description' y 'category', y 101 tiene Python y análisis de datos,
        # es probable que sea más alto.
        assert scores[101] >= scores[102], "El taller de Python (101) debería tener un puntaje igual o mayor para este perfil que Limpieza de Playa (102)."

def test_inclusivity_and_disability_consideration(app):
    """
    Prueba cómo se consideran la inclusividad y las discapacidades del usuario.
    Un programa inclusivo y que apoya la discapacidad del usuario debería tener un puntaje aumentado.
    """
    user_profile_con_discapacidad = {
        'id': 2,
        'interests': ['lectura', 'educación'],
        'skills': ['enseñanza'],
        'disabilities': ['Visual'] # Usuario con discapacidad visual
    }
    programs = [
        {
            'id': 201,
            'name': 'Club de Lectura General',
            'description': 'Un club de lectura para todos.',
            'category': 'cultura',
            'es_inclusiva': False, # No específicamente inclusivo
            'discapacidades_soportadas': []
        },
        {
            'id': 202,
            'name': 'Club de Lectura Adaptado',
            'description': 'Club de lectura con materiales en braille y audiolibros.',
            'category': 'cultura',
            'es_inclusiva': True, # Es inclusivo
            'discapacidades_soportadas': ['Visual', 'Auditiva'] # Soporta discapacidad visual
        },
        {
            'id': 203,
            'name': 'Taller de Jardinería',
            'description': 'Aprende sobre plantas.',
            'category': 'naturaleza',
            'es_inclusiva': True, # Es inclusivo pero no relacionado con la discapacidad del usuario
            'discapacidades_soportadas': ['Motriz']
        }
    ]

    scores = get_compatibility_scores(user_profile_con_discapacidad, programs)

    assert isinstance(scores, dict)
    assert 201 in scores and 202 in scores and 203 in scores

    # El programa 202 es inclusivo Y soporta la discapacidad del usuario, debería tener el puntaje más alto
    # o al menos significativamente más alto que 201.
    # El programa 203 es inclusivo pero para otra discapacidad, podría tener un ligero aumento sobre 201.

    # Asumimos que la base de similitud de texto para 201 y 202 es similar (ambos clubes de lectura)
    # El ajuste por discapacidad debería hacer 202 > 201
    assert scores[202] > scores[201], "El club adaptado (202) debería tener mayor puntaje que el general (201) por la discapacidad."

    # Es más difícil comparar 203 con 201 o 202 directamente sin conocer la base de similitud de texto.
    # Pero, si la similitud de texto de 203 fuera comparable a 201, el ajuste de inclusividad
    # (aunque no para la discapacidad específica del usuario) podría hacerlo mayor que 201.
    # Para esta prueba, nos enfocamos en la clara diferencia entre 201 y 202.

    # Verificamos que los puntajes estén en rango
    for score in scores.values():
        assert 0 <= score <= 100

def test_empty_or_invalid_inputs(app):
    """
    Prueba el comportamiento de la función con entradas vacías o inválidas.
    Debería devolver un diccionario vacío en estos casos.
    """
    user_profile_valido = {'id': 1, 'interests': ['a'], 'skills': ['b'], 'disabilities': []}
    program_valido = [{'id': 101, 'description': 'd', 'category': 'c'}]

    # Perfil de usuario vacío o None
    assert get_compatibility_scores({}, program_valido) == {}, "Perfil vacío debería devolver diccionario vacío."
    assert get_compatibility_scores(None, program_valido) == {}, "Perfil None debería devolver diccionario vacío."

    # Lista de programas vacía o None
    assert get_compatibility_scores(user_profile_valido, []) == {}, "Lista de programas vacía debería devolver dict vacío."
    assert get_compatibility_scores(user_profile_valido, None) == {}, "Lista de programas None debería devolver dict vacío."

    # Ambas entradas inválidas
    assert get_compatibility_scores(None, None) == {}, "Ambas entradas None deberían devolver dict vacío."
    assert get_compatibility_scores({}, []) == {}, "Ambas entradas vacías deberían devolver dict vacío."

    # Perfil de usuario sin campos de texto relevantes
    user_profile_sin_texto = {'id': 3, 'disabilities': ['Auditiva']} # Sin intereses ni habilidades
    # Esto debería ser manejado por la lógica interna que retorna scores vacíos si user_text está vacío.
    scores_sin_texto_usuario = get_compatibility_scores(user_profile_sin_texto, program_valido)
    assert scores_sin_texto_usuario == {}, "Usuario sin intereses/habilidades debería resultar en scores vacíos."


def test_program_without_description_or_category(app):
    """
    Prueba con programas que tienen descripción o categoría como None o string vacío.
    La función debería manejar esto sin errores y asignar un puntaje (posiblemente 0 o bajo).
    """
    user_profile = {
        'id': 1,
        'interests': ['deporte'],
        'skills': ['organización'],
        'disabilities': []
    }
    programs = [
        {'id': 301, 'name': 'Partido de Futbol', 'description': None, 'category': 'deporte', 'es_inclusiva': False, 'discapacidades_soportadas': []},
        {'id': 302, 'name': 'Yoga al Aire Libre', 'description': 'Sesión de yoga relajante.', 'category': None, 'es_inclusiva': False, 'discapacidades_soportadas': []},
        {'id': 303, 'name': 'Torneo de Ajedrez', 'description': '', 'category': 'estrategia', 'es_inclusiva': False, 'discapacidades_soportadas': []},
        {'id': 304, 'name': 'Meditación Guiada', 'description': 'Encuentra tu paz interior.', 'category': '', 'es_inclusiva': False, 'discapacidades_soportadas': []},
        {'id': 305, 'name': 'Evento Cultural Anónimo', 'description': None, 'category': None, 'es_inclusiva': False, 'discapacidades_soportadas': []}
    ]

    scores = get_compatibility_scores(user_profile, programs)

    assert isinstance(scores, dict)
    assert len(scores) == len(programs)

    for program in programs:
        program_id = program['id']
        assert program_id in scores, f"El ID del programa {program_id} debe estar en los puntajes."
        score = scores[program_id]
        assert 0 <= score <= 100, f"El puntaje para el programa {program_id} ({score}) debe estar entre 0 y 100."

        # Si un programa no tiene ni descripción ni categoría, su texto base será vacío.
        # La similitud coseno con cualquier perfil de usuario será 0 o indefinida (manejada como 0 por el servicio).
        if program_id == 305:
            assert scores[program_id] == 0.0, "Programa sin descripción ni categoría debería tener puntaje 0."
        # Para los otros, es esperable un puntaje, aunque podría ser bajo si la información es parcial.
        elif program_id == 301 and scores[program_id] > 0: # Tiene categoría 'deporte', coincide con interés
             pass # Es esperable que tenga algún puntaje > 0
        elif program_id == 302 and scores[program_id] >= 0: # No tiene categoría, pero sí descripción
             pass
        elif program_id == 303 and scores[program_id] >= 0: # Tiene categoría pero desc vacía
             pass
        elif program_id == 304 and scores[program_id] >= 0: # Tiene desc pero cat vacía
             pass

def test_program_with_non_list_disabilities_supported(app):
    """
    Prueba que un programa con 'discapacidades_soportadas' no siendo una lista
    sea manejado correctamente (debería ser tratado como una lista vacía).
    """
    user_profile = {
        'id': 1,
        'interests': ['ayuda social'],
        'skills': ['comunicación'],
        'disabilities': ['Motriz']
    }
    programs = [
        {
            'id': 401,
            'name': 'Visita a Hogar de Ancianos',
            'description': 'Compartir tiempo con personas mayores.',
            'category': 'ayuda social',
            'es_inclusiva': True,
            'discapacidades_soportadas': "Motriz" # Formato incorrecto (string en lugar de lista)
        },
         {
            'id': 402,
            'name': 'Recaudación de Fondos',
            'description': 'Ayuda a recaudar fondos para caridad.',
            'category': 'ayuda social',
            'es_inclusiva': True,
            'discapacidades_soportadas': None # Formato incorrecto (None en lugar de lista)
        }
    ]

    scores = get_compatibility_scores(user_profile, programs)

    assert isinstance(scores, dict)
    assert 401 in scores
    assert 402 in scores
    # El servicio internamente convierte 'discapacidades_soportadas' a lista vacía si no es una lista.
    # Por lo tanto, para el usuario con discapacidad 'Motriz', el programa 401, a pesar de tener "Motriz"
    # como string, no debería bonificar adicionalmente por la discapacidad específica, solo por ser 'es_inclusiva'.
    # Lo mismo para 402.
    # La prueba principal es que no falle y devuelva puntajes válidos.
    assert 0 <= scores[401] <= 100
    assert 0 <= scores[402] <= 100

    # Si la similitud base es alta, y 'es_inclusiva' da +5, y la discapacidad específica da +10:
    # Un programa que no es inclusivo podría tener X.
    # Un programa que es inclusivo pero no soporta la discapacidad específica del usuario: X + 5.
    # Un programa que es inclusivo y soporta la discapacidad específica: X + 5 + 10.
    # En este caso, como 'discapacidades_soportadas' se trata como [], el puntaje solo debería reflejar
    # el aumento por 'es_inclusiva', no el aumento adicional por la discapacidad específica.
    # Esto es difícil de probar con precisión sin conocer X, pero podemos verificar que no sea un puntaje máximo
    # si la similitud de texto no es perfecta.

    # Para simplificar, esta prueba se enfoca en la robustez (no error) y que los puntajes son válidos.
    # La lógica interna de corrección de 'discapacidades_soportadas' es lo que se prueba implícitamente.

# (Este es un ejemplo de prueba que puede requerir un mock si el servicio hiciera llamadas externas o tuviera dependencias complejas)
# def test_example_with_mock(app, mocker):
#     # Suponiendo que get_compatibility_scores usa alguna función externa que queremos mockear
#     # mock_external_call = mocker.patch('services.compatibility_service.nombre_funcion_externa')
#     # mock_external_call.return_value = "valor mockeado"
#     # ... luego llamar a get_compatibility_scores y assertar ...
#     pass
