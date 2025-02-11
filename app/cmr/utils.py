def clean_table_name(table_name):
    """Takes in various randomly formatted table names such as 'Gcmd Platform', 'gcmd_platform'
    and 'GcmdPlatform' and standardizes them all to 'gcmdplatform' for comparison purposes.

    Args:
        table_name (str): Randomly formatted table_name, such as 'gcmd_platform' or 'GcmdPlatform'

    Returns:
        table_name (str): Uniformly formatted table_name, such as 'gcmdplatform'
    """

    table_name = table_name.lower()
    table_name = table_name.replace(' ', '')
    table_name = table_name.replace('_', '')

    return table_name


def purify_list(dirty_list, lower=True):
    """Takes a dirty list and removes duplicates, converts to lowercase,
    and removes null values.

    Args:
        dirty_list (list): List with duplicate, uppercase, or null values

    Returns:
        list: clean list with no duplicates, uppercase, or null values
    """

    if lower:
        clean_set = set(i.lower() for i in dirty_list if i)
    else:
        clean_set = set(i for i in dirty_list if i)

    return clean_set
