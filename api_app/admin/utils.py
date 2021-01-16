from django.forms import Field


def prefix_field(field: Field, field_name_prefix: str) -> None:
    """
    Mutate a provided field so that its rendered inputs have a name prefixed
    with the provided field name prefix.
    """
    renderer = field.widget.render

    def _widget_render_wrapper(name, *args, **kwargs):
        return renderer(f"{field_name_prefix}{name}", *args, **kwargs)

    field.widget.render = _widget_render_wrapper
