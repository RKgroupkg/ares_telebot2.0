def check_id_in_list(id_to_check, id_list):
    """
    Checks if the given ID (string or integer) is in the list of IDs.
    
    Args:
    id_to_check (str or int): The ID to check.
    id_list (list): The list of IDs (can contain strings and/or integers).
    
    Returns:
    bool: True if the ID is in the list, False otherwise.
    """
    try:
        if not isinstance(id_list, list):
            raise ValueError("Error: The second argument must be a list.")
        
        return id_to_check in id_list
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
