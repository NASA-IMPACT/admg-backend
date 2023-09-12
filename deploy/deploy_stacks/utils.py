def generate_name(name, stage):
    if not name:
        raise ValueError("Name cannot be blank")
    return f"admg-{stage}-{name}".lower()
