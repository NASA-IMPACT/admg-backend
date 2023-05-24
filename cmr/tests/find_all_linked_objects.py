from collections import deque


def get_all_related_objects(obj):
    """
    Get all objects related to the given object, including through multiple layers of relationships.
    """
    related_objects = []

    # Create a queue to keep track of objects to process
    queue = deque([obj])

    while queue:
        # Pop an object from the queue
        current_obj = queue.popleft()

        # Get all related fields
        related_fields = [
            f
            for f in current_obj._meta.get_fields()
            if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
        ]

        # Traverse each related field to get all related objects
        for related_field in related_fields:
            related_name = related_field.get_accessor_name()

            # Check if the field is one-to-one or one-to-many
            if related_field.one_to_one:
                try:
                    related_obj = getattr(current_obj, related_name)
                except related_field.related_model.DoesNotExist:
                    related_obj = None
                if related_obj and related_obj not in related_objects:
                    related_objects.append(related_obj)
                    queue.append(related_obj)
            else:
                # Get the related objects for this field
                related_obj_list = list(getattr(current_obj, related_name).all())
                for related_obj in related_obj_list:
                    if related_obj and related_obj not in related_objects:
                        related_objects.append(related_obj)
                        queue.append(related_obj)

    return related_objects
