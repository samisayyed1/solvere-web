from app.utils import get_user


def greet(user_id: int) -> str:
    return f"hello {get_user(user_id)}"


if __name__ == "__main__":
    print(greet(1))
