import random
from model.models import Inscripciones, Usuarios, Actividades, Recomendaciones, TipoRecomendacion, db
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import func

def get_compatibility_scores(user_profile, programs_or_activities):
    """
    Placeholder for fetching compatibility scores from a Colab prediction service.
    
    Args:
        user_profile (dict): A dictionary representing the user's profile.
                             Example: {'id': 1, 'interests': ['environment', 'education'], 'skills': ['python', 'project management']}
        programs_or_activities (list): A list of dictionaries, where each dictionary
                                       represents a program or activity.
                                       Example: [{'id': 101, 'name': 'Beach Cleanup', 'required_skills': ['manual labor']}, ...]
                                       
    Returns:
        dict: A dictionary mapping item_id to a compatibility score (e.g., 0.0 to 100.0).
              Returns an empty dictionary if input is invalid or service fails.
    """
    print(f"Attempting to get compatibility for user: {user_profile.get('id', 'Unknown User')}")
    # print(f"User profile details: {user_profile}") # Could be verbose
    # print(f"With items: {[item.get('id', 'Unknown Item') for item in programs_or_activities]}") # Could be verbose

    # TODO: Replace with actual API call to Colab service.
    # This will involve:
    # 1. Preparing the payload based on the Colab API's expected input format.
    # 2. Making an HTTP POST request (e.g., using the 'requests' library).
    #    API_ENDPOINT = "YOUR_COLAB_API_ENDPOINT_HERE"
    #    try:
    #        response = requests.post(API_ENDPOINT, json={'user': user_profile, 'items': programs_or_activities})
    #        response.raise_for_status() # Raise an exception for bad status codes
    #        return response.json().get('scores', {}) # Assuming scores are under a 'scores' key
    #    except requests.exceptions.RequestException as e:
    #        print(f"API request failed: {e}")
    #        return {} # Return empty scores on failure

    # Mock response: return a dictionary mapping item_id to a random compatibility score
    scores = {}
    if not programs_or_activities or not isinstance(programs_or_activities, list):
        return scores
        
    for item in programs_or_activities:
        if isinstance(item, dict) and 'id' in item:
            # Simulate some basic matching based on interests (if available)
            base_score = random.uniform(0.3, 0.7)
            if user_profile.get('interests') and item.get('category'): # Assuming item has a 'category'
                if any(interest in item['category'].lower() for interest in user_profile['interests']):
                    base_score += random.uniform(0.1, 0.25) # Boost if interest matches category
            
            scores[item.get('id')] = round(min(base_score, 0.95) * 100, 1) # Percentage, capped
        else:
            print(f"Skipping invalid item: {item}")
            
    print(f"Mock scores generated: {scores}")
    return scores

def generate_user_based_recommendations(target_user_id=None):
    """
    Generates user-based collaborative filtering recommendations.
    If target_user_id is provided, generates for that specific user.
    Otherwise, potentially for all users (currently focused on target_user_id).
    """
    print("Starting user-based recommendation generation...")

    # Fetch Data
    all_inscriptions_tuples = db.session.query(Inscripciones.id_usuario, Inscripciones.id_actividad).all()
    if not all_inscriptions_tuples:
        print("No inscriptions data found. Cannot generate recommendations.")
        return

    print(f"Fetched {len(all_inscriptions_tuples)} inscriptions from the database.")

    # Create User-Item Matrix
    df_inscriptions = pd.DataFrame(all_inscriptions_tuples, columns=['user_id', 'item_id'])
    user_item_matrix = pd.crosstab(df_inscriptions['user_id'], df_inscriptions['item_id'])

    if user_item_matrix.empty:
        print("User-item matrix is empty after processing inscriptions.")
        return

    print("User-item matrix created successfully:")
    print(user_item_matrix.head())

    # Calculate Cosine Similarity
    user_similarity_matrix = cosine_similarity(user_item_matrix)
    user_similarity_df = pd.DataFrame(user_similarity_matrix, index=user_item_matrix.index, columns=user_item_matrix.index)

    print("User similarity matrix calculated successfully:")
    print(user_similarity_df.head())

    users_to_process = [target_user_id] if target_user_id else user_item_matrix.index

    if target_user_id and target_user_id not in user_item_matrix.index:
        print(f"Target user ID {target_user_id} not found in the user-item matrix. No recommendations can be generated for this user.")
        return

    print(f"Processing recommendations for user(s): {users_to_process}")

    for user_id in users_to_process:
        print(f"\nGenerating recommendations for user_id: {user_id}")

        # Get top N similar users (e.g., N=5), excluding the user itself
        N = 5
        # Ensure user_id is in similarity dataframe columns before proceeding
        if user_id not in user_similarity_df.columns:
            print(f"User ID {user_id} not found in similarity matrix columns. Skipping.")
            continue

        # Get similarity scores for the current user, sort them, and exclude self
        user_similarities = user_similarity_df[user_id].sort_values(ascending=False)

        # Filter out users with similarity score of 0 or less, and also exclude self
        # Self is typically at index 0 with score 1.0 after sorting
        similar_users_filtered = user_similarities[user_similarities > 0][1:] # Exclude self (index 0) and scores <= 0

        # Take top N from the filtered list
        similar_users = similar_users_filtered.head(N).index

        print(f"Top {N} similar users (with score > 0) for {user_id}: {list(similar_users)}")

        if not list(similar_users):
            print(f"No users with similarity > 0 found for user {user_id}. Skipping recommendation generation for this user.")
            continue

        # Get activities the user_id has participated in
        participated_activities = user_item_matrix.loc[user_id][user_item_matrix.loc[user_id] > 0].index
        print(f"User {user_id} participated in activities: {list(participated_activities)}")

        for similar_user_id in similar_users:
            print(f"Processing similar user: {similar_user_id}")

            # Get activities the similar_user participated in
            similar_user_activities = user_item_matrix.loc[similar_user_id][user_item_matrix.loc[similar_user_id] > 0].index
            print(f"Similar user {similar_user_id} participated in: {list(similar_user_activities)}")

            # Find new recommendations (activities similar user did, but target user didn't)
            new_recommendations = similar_user_activities.difference(participated_activities)
            print(f"New potential recommendations from {similar_user_id} for {user_id}: {list(new_recommendations)}")

            for activity_id in new_recommendations:
                # Store in Recomendaciones table
                existing_rec = Recomendaciones.query.filter_by(
                    id_usuario=user_id,
                    id_actividad=activity_id,
                    tipo_recomendacion=TipoRecomendacion.PERSONALIZADA
                ).first()

                if not existing_rec:
                    recommendation_score = user_similarity_df.loc[user_id, similar_user_id]

                    new_rec_entry = Recomendaciones(
                        id_usuario=user_id,
                        id_actividad=activity_id,
                        tipo_recomendacion=TipoRecomendacion.PERSONALIZADA,
                        score=recommendation_score, # Store score in the new field
                        descripcion="Generated by user-based collaborative filtering" # New description
                    )
                    db.session.add(new_rec_entry)
                    print(f"Stored recommendation: User {user_id}, Activity {activity_id}, Score: {recommendation_score:.4f}, Desc: {new_rec_entry.descripcion}")
                else:
                    print(f"Recommendation already exists for User {user_id}, Activity {activity_id}. Skipping.")

    try:
        db.session.commit()
        print("Successfully committed recommendations to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing recommendations to database: {e}")

    print("User-based recommendation generation finished.")

def get_recommendations_for_user(user_id, limit=10):
    """
    Retrieves stored recommendations for a specific user.

    Args:
        user_id (int): The ID of the user for whom to fetch recommendations.
        limit (int): The maximum number of recommendations to return.

    Returns:
        list: A list of recommended activity IDs, ordered by score (descending).
    """
    print(f"Fetching recommendations for user_id: {user_id} with limit: {limit}")

    recommendations = Recomendaciones.query.filter_by(
        id_usuario=user_id,
        tipo_recomendacion=TipoRecomendacion.PERSONALIZADA
    ).order_by(
        Recomendaciones.score.desc() # Order by the new numeric score field
    ).limit(limit).all()

    if not recommendations:
        print(f"No recommendations found for user {user_id}.")
        return []

    # Extract activity IDs
    # Scores are now directly in rec.score and sorted by the database.
    # No need to parse from description.

    recommended_activity_ids = [rec.id_actividad for rec in recommendations]

    print(f"Returning {len(recommended_activity_ids)} recommendations for user {user_id}: {recommended_activity_ids}")
    return recommended_activity_ids

def get_top_recommended_activities(limit=10):
    """
    Retrieves the top N most frequently recommended activities.
    These are activities that appear most often in the PERSONALIZADA recommendations
    across all users.

    Args:
        limit (int): The maximum number of top activities to return.

    Returns:
        list: A list of Actividades objects that are most frequently recommended.
    """
    print(f"Fetching top {limit} recommended activities...")

    top_activities_data = db.session.query(
        Recomendaciones.id_actividad,
        func.count(Recomendaciones.id_actividad).label('recommendation_count')
    ).filter(
        Recomendaciones.tipo_recomendacion == TipoRecomendacion.PERSONALIZADA
    ).group_by(
        Recomendaciones.id_actividad
    ).order_by(
        func.count(Recomendaciones.id_actividad).desc()
    ).limit(limit).all()

    if not top_activities_data:
        print("No recommended activities found.")
        return []

    print(f"Top activities data (id, count): {top_activities_data}")

    activity_ids = [data.id_actividad for data in top_activities_data]

    if not activity_ids:
        print("No activity IDs extracted from top_activities_data.")
        return []

    top_activities_objects = Actividades.query.filter(Actividades.id_actividad.in_(activity_ids)).all()

    # Optional: Re-order these objects based on the recommendation_count,
    # as the .in_() query doesn't preserve the order from top_activities_data.
    # Create a mapping from id to count for sorting.
    activity_id_to_count_map = {data.id_actividad: data.recommendation_count for data in top_activities_data}

    # Sort the activity objects based on the recommendation_count
    # Python's sort is stable, so if counts are equal, original relative order (if any) is maintained.
    # However, the order from Actividades.query is not guaranteed.
    # To ensure order from `top_activities_data` (which is by count desc):
    sorted_top_activities_objects = sorted(
        top_activities_objects,
        key=lambda act: activity_id_to_count_map.get(act.id_actividad, 0),
        reverse=True
    )

    print(f"Returning {len(sorted_top_activities_objects)} Actividades objects.")
    return sorted_top_activities_objects
