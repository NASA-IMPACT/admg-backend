def get_diff(old_obj, new_obj):
    """
    Generates diff for change object

    Args:
        old_obj (dict) : the old object
        new_obj (dict) : the new changed object

    Returns:
        dict : the changed keys
    """
    diff_obj = {}
    for key in old_obj:
        if key in new_obj and new_obj[key] != old_obj[key]:
            diff_obj[key] = new_obj[key]
        elif key not in new_obj:
            raise Exception("The old key is not present in the new object")
        
    return diff_obj
