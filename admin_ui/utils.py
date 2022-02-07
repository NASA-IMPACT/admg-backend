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
        old_item = " ".join(str(old_item).strip().split())
        new_item = " ".join(str(new_item).strip().split())

    return old_item == new_item


def disable_form_fields(form):
    for fieldname in form.fields:
        form.fields[fieldname].disabled = True
    return form
