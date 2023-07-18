STAGE = "dev"


def generate_name(name):
    if not name:
        raise ValueError("Name cannot be blank")
    return f"admg-{STAGE}-{name}".lower()
