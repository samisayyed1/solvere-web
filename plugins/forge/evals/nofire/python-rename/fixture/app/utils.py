"""Small user helpers."""

USERS = {1: "ada", 2: "grace"}


def get_user(user_id: int) -> str:
    """Return the user name for an id."""
    return USERS[user_id]
