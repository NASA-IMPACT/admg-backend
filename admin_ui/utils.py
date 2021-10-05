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


def compare_values(old_item, new_item):
    """
    Compare old item with new item

    Args:
        old_item (dict) : the old item
        new_item (dict) : the new item

    Returns:
        boolean: True or False based on if the values have changed or not
    """
    if isinstance(old_item, list):
        old_item = [str(item) for item in old_item]
        new_item = [str(item) for item in new_item]
    elif not isinstance(old_item, str):
        old_item = str(old_item).strip()
        new_item = str(new_item).strip()
    else:
        old_item = " ".join(old_item.strip().split())
        new_item = " ".join(new_item.strip().split())

    return old_item == new_item
