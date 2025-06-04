import random

# TODO: If a real API call is implemented, 'requests' library might be needed.

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

    # TODO: Replace with actual API call to Colab service.
    scores = {}
    if not programs_or_activities or not isinstance(programs_or_activities, list):
        return scores

    num_activities = len(programs_or_activities)

    for index, item in enumerate(programs_or_activities):
        if isinstance(item, dict) and 'id' in item:
            item_id = item.get('id')
            if index == 0 and num_activities >= 1:
                scores[item_id] = round(random.uniform(70, 80), 1)
            elif index == 1 and num_activities >= 2:
                scores[item_id] = round(random.uniform(55, 65), 1)
            else:
                base_score = random.uniform(0.4, 0.75)
                if user_profile.get('interests') and item.get('category'): # Assuming item has a 'category'
                    if any(interest in item['category'].lower() for interest in user_profile['interests']):
                        base_score += random.uniform(0.1, 0.25)
                scores[item_id] = round(min(base_score, 0.95) * 100, 1)
        else:
            print(f"Skipping invalid item: {item}")

    print(f"Mock scores generated: {scores}")
    return scores
