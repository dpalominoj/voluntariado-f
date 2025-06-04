import random

# TODO: If a real API call is implemented, 'requests' library might be needed.
# import requests

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
