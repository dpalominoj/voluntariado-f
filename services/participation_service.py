"""
Service module for predicting activity participation levels.

This module provides functions to:
- Extract features for a given activity (`obtener_features`).
- Train a RandomForest model and predict the probability of high participation
  for a specific activity (`predecir_participacion`).
"""

from model.models import Inscripciones, Actividades, db # Removed: Usuarios, Recomendaciones, TipoRecomendacion
import pandas as pd
# from sklearn.metrics.pairwise import cosine_similarity # Removed
# from sqlalchemy import func, create_engine # Removed func, create_engine
# from sqlalchemy.orm import sessionmaker # Removed sessionmaker
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import export_graphviz
from sklearn.model_selection import train_test_split
# from database.datos_iniciales import seed_data # For initial data, if needed during setup

# Note: 'Usuarios' was removed from model.models import as it's not used in the remaining functions.
# 'create_engine', 'sessionmaker', 'cosine_similarity', 'func' were also removed as they are no longer used.

def obtener_features(actividad_id):
    """
    Obtiene y calcula características (features) de una actividad específica.

    Estas características se utilizan como entrada para el modelo de predicción
    de participación.

    Args:
        actividad_id (int): El ID de la actividad para la cual obtener features.

    Returns:
        dict or None: Un diccionario con las siguientes características:
            - "current_inscriptions" (int): Número actual de inscritos.
            - "cupo_maximo" (int): Capacidad máxima de la actividad.
            - "historico_similar" (float): Placeholder para participación histórica
                                           en actividades similares (actualmente 0.5).
            - "habilidades_voluntarios" (int): Placeholder para el nivel/cantidad
                                               de habilidades de voluntarios
                                               requeridas/disponibles (actualmente 3).
        Retorna None si la actividad no se encuentra.
    """
    actividad = Actividades.query.get(actividad_id)
    if not actividad:
        print(f"Actividad con ID {actividad_id} no encontrada.")
        return None

    cupo_maximo = actividad.cupo_maximo
    current_inscriptions = Inscripciones.query.filter_by(id_actividad=actividad_id).count()

    # Placeholder features - to be replaced with more sophisticated logic
    historico_similar = 0.5  # Average historical participation
    habilidades_voluntarios = 3  # Average skill level or count

    features = {
        "current_inscriptions": current_inscriptions,
        "cupo_maximo": cupo_maximo,
        "historico_similar": historico_similar,
        "habilidades_voluntarios": habilidades_voluntarios
    }
    return features

def predecir_participacion(actividad_id):
    """
    Predice la probabilidad de alta participación para una actividad específica.

    El proceso incluye:
    1. Obtener características para la actividad objetivo.
    2. Preparar datos de entrenamiento:
        - Obtener características para todas las actividades históricas.
        - Crear una variable objetivo ('y') basada en un proxy:
          Se considera 'alta participación' (1) si la ocupación actual
          (inscripciones / cupo_maximo) es >= 60%, de lo contrario 'baja' (0).
          Esta es una simplificación y podría necesitar ajustes.
    3. Manejar datos insuficientes (si hay menos de 10 muestras o solo una clase,
       devuelve una predicción por defecto).
    4. Entrenar un modelo RandomForestClassifier con los datos históricos.
       El modelo se re-entrena con cada llamada a esta función.
    5. Generar una predicción de probabilidad para la actividad objetivo.
    6. Opcionalmente, exportar una visualización del primer árbol del modelo
       a un archivo .dot (si Graphviz está disponible).
    7. Calcular métricas básicas (accuracy) sobre un conjunto de prueba.

    Args:
        actividad_id (int): El ID de la actividad para la cual predecir la participación.

    Returns:
        dict: Un diccionario conteniendo:
            - 'probabilidad' (float): La probabilidad predicha de alta participación (clase 1).
                                     Puede ser una probabilidad por defecto si el modelo no se entrena.
            - 'metricas' (dict or str): Un diccionario con métricas como 'accuracy',
                                        o un string indicando por qué no se calcularon
                                        (e.g., "No training data", "Insufficient data for training").
            - 'tree_dot_file' (str or None): Nombre del archivo .dot generado para la visualización
                                             del árbol (e.g., "tree.dot"), o None si no se generó.
            - 'error' (str, opcional): Un mensaje de error si ocurrió un problema crítico.
            - 'info' (str, opcional): Un mensaje informativo, especialmente si se devuelve
                                     una predicción por defecto debido a datos insuficientes.
    """
    print(f"Iniciando predicción de participación para actividad_id: {actividad_id}")

    # 1. Obtener features para la actividad específica que queremos predecir
    target_activity_features_dict = obtener_features(actividad_id)
    if target_activity_features_dict is None:
        print(f"No se pudieron obtener features para la actividad {actividad_id}. Abortando.")
        return {"error": "Activity features not found."}

    # Convertir las features de la actividad específica a DataFrame para la predicción
    # Asegurar el orden de las columnas sea el mismo que el usado en el entrenamiento
    feature_names = ['current_inscriptions', 'cupo_maximo', 'historico_similar', 'habilidades_voluntarios']
    try:
        target_activity_df = pd.DataFrame([target_activity_features_dict], columns=feature_names)
    except Exception as e:
        print(f"Error al crear DataFrame para actividad específica: {e}")
        return {"error": "Failed to create DataFrame for target activity."}


    # 2. Preparar datos de entrenamiento del histórico de actividades
    all_activities = Actividades.query.all()
    if not all_activities:
        print("No hay actividades en la base de datos para entrenar el modelo.")
        return {"probabilidad": 0.5, "metricas": "No training data", "tree_dot_file": None, "info": "Default prediction due to no activities."}

    X_data = []
    y_data = []

    print(f"Procesando {len(all_activities)} actividades para datos de entrenamiento.")
    for activity in all_activities:
        features_dict = obtener_features(activity.id_actividad)
        if features_dict:
            X_data.append(features_dict)
            # Definir target 'y': 1 si ocupación >= 60%, else 0
            if features_dict['cupo_maximo'] > 0:
                ocupacion = features_dict['current_inscriptions'] / features_dict['cupo_maximo']
                y_data.append(1 if ocupacion >= 0.6 else 0)
            else:
                y_data.append(0) # Si cupo_maximo es 0, participación baja

    if not X_data:
        print("No se pudieron extraer features para ninguna actividad de entrenamiento.")
        return {"probabilidad": 0.5, "metricas": "No training data", "tree_dot_file": None, "info": "Default prediction due to no feature data."}

    X_df = pd.DataFrame(X_data, columns=feature_names)
    y_series = pd.Series(y_data)

    # 3. Manejar datos insuficientes para el entrenamiento
    MIN_SAMPLES_FOR_TRAINING = 10 # Umbral mínimo de muestras
    if len(X_df) < MIN_SAMPLES_FOR_TRAINING or len(y_series.unique()) < 2:
        print(f"Datos insuficientes para entrenar el modelo. Muestras: {len(X_df)}, Clases: {len(y_series.unique()) if X_data else 0}.")
        # Devolver una predicción por defecto si no se puede entrenar
        # La probabilidad podría basarse en la media de 'y_data' si hay datos, o 0.5 si no.
        default_proba = y_series.mean() if len(y_series) > 0 and len(y_series.unique()) == 1 else 0.5
        return {"probabilidad": default_proba,
                "metricas": "Insufficient data for training",
                "tree_dot_file": None,
                "info": f"Default prediction. Samples: {len(X_df)}, Classes: {len(y_series.unique()) if X_data else 0}"}

    print(f"Datos de entrenamiento preparados: {X_df.shape[0]} muestras.")

    # 4. Entrenar el modelo
    try:
        X_train, X_test, y_train, y_test = train_test_split(X_df, y_series, test_size=0.2, random_state=42, stratify=y_series if len(y_series.unique()) > 1 else None)
        modelo = RandomForestClassifier(random_state=42, class_weight='balanced') # class_weight puede ayudar con desbalanceo
        modelo.fit(X_train, y_train)
        print("Modelo RandomForestClassifier entrenado exitosamente.")
    except Exception as e:
        print(f"Error durante el entrenamiento del modelo: {e}")
        # Podríamos devolver una predicción basada en la media si el entrenamiento falla
        return {"probabilidad": y_series.mean(), "metricas": f"Training error: {e}", "tree_dot_file": None, "info": "Default prediction due to training error."}

    # 5. Generar predicción para la actividad específica
    try:
        # Asegurar que target_activity_df tenga las mismas columnas y en el mismo orden que X_df
        target_activity_df = target_activity_df[X_df.columns]
        proba = modelo.predict_proba(target_activity_df)[0][1] # Probabilidad de la clase '1' (alta participación)
        print(f"Predicción de probabilidad para actividad {actividad_id}: {proba}")
    except Exception as e:
        print(f"Error durante la predicción para la actividad {actividad_id}: {e}")
        return {"error": f"Prediction error: {e}"}


    # 6. Exportar visualización de un árbol de decisión (opcional)
    tree_dot_file_path = 'tree.dot'
    try:
        estimator = modelo.estimators_[0] # Selecciona el primer árbol del bosque
        export_graphviz(estimator, out_file=tree_dot_file_path,
                        feature_names=X_df.columns,
                        class_names=['Baja', 'Alta'], # Asumiendo 0: Baja, 1: Alta
                        rounded=True, proportion=False, precision=2, filled=True)
        print(f"Visualización del árbol de decisión guardada en: {tree_dot_file_path}")
    except Exception as e:
        print(f"Error al exportar el árbol de decisión: {e}. Graphviz podría no estar instalado.")
        tree_dot_file_path = None # Indicar que no se pudo generar

    # 7. Calcular métricas (ejemplo básico de accuracy)
    try:
        accuracy = modelo.score(X_test, y_test)
        metricas = {"accuracy": accuracy}
        print(f"Métricas del modelo: {metricas}")
    except Exception as e:
        print(f"Error al calcular métricas: {e}")
        metricas = {"accuracy": "Error calculating metrics"}


    # 8. Retornar resultados
    return {
        'probabilidad': proba,
        'metricas': metricas,
        'tree_dot_file': tree_dot_file_path
    }
