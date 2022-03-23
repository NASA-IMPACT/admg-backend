from django.forms import FileField, ModelForm


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


def serialize_model_form(model_form: ModelForm):
    """
    Given a model form, serialize and export the data to a format
    usable as a change.update field
    """
    update = {}
    for name, field in model_form.fields.items():
        if isinstance(field, FileField):
            # Save any uploaded files to disk, then overwrite their values with their name
            model_field = getattr(model_form.instance, name)
            if not model_field._file:
                continue
            model_field.save(model_field.url, model_form.cleaned_data[name])
            update[name] = model_field.name

        else:
            # Populate Change's form with values from destination model's form.
            # We're not saving the cleaned_data because we want the raw text, not
            # the processed values (e.g. we don't want Polygon objects for bounding
            # boxes, rather we want the raw polygon text). This may or may not be
            # the best way to achieve this.
            update[name] = field.widget.value_from_datadict(
                model_form.data, model_form.files, model_form.add_prefix(name)
            )
    return update
