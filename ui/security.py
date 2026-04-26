import keyring

APP = "loganalyzer"

def save_tokens(access: str, refresh: str):
    keyring.set_password(APP, "access_token", access)
    keyring.set_password(APP, "refresh_token", refresh)

def load_tokens() -> dict | None:
    access  = keyring.get_password(APP, "access_token")
    refresh = keyring.get_password(APP, "refresh_token")
    if access and refresh:
        return {"access": access, "refresh": refresh}
    return None

def clear_tokens():
    keyring.delete_password(APP, "access_token")
    keyring.delete_password(APP, "refresh_token")