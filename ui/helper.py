
# import os

# import requests

# BASE_URL = "http://127.0.0.1:8000"

# session = requests.Session()
# session.headers.update({"Content-Type": "application/json"})


# def set_token(access_token: str):
#     """Call once after login. All future api() calls send it automatically."""
#     if access_token:
#         session.headers["Authorization"] = f"Bearer {access_token}"
#     else:
#         session.headers.pop("Authorization", None)


# def clear_token():
#     """Call on logout to remove the token from the session."""
#     session.headers.pop("Authorization", None)


# def api(method: str, path: str, **kwargs):
#     url = BASE_URL.rstrip("/") + path
#     resp = session.request(method.upper(), url, timeout=10, **kwargs)
#     resp.raise_for_status()
#     return resp.json()



# def upload(path: str, filepath: str) -> dict:
#     url = BASE_URL.rstrip("/") + path
#     token = session.headers.get("Authorization")
#     headers = {"Authorization": token} if token else {}

#     with open(filepath, "rb") as fh:
#         fname = os.path.basename(filepath)
#         resp = requests.post(
#             url,
#             files={"file": (fname, fh)},
#             headers=headers,
#             timeout=60,
#         )
#     resp.raise_for_status()
#     return resp.json()



import os
import requests
from requests import Session, Response
from security import load_tokens, save_tokens, clear_tokens

BASE_URL = "http://127.0.0.1:8000"


class AutoRefreshSession(Session):
    def __init__(self):
        super().__init__()
        self.headers.update({"Content-Type": "application/json"})
        self._refreshing = False      

    def send(self, request, **kwargs) -> Response:
        resp = super().send(request, **kwargs)
        if resp.status_code != 401 or self._refreshing:
            return resp

        new_token = self._refresh()
        if not new_token:
            return resp               

        request.headers["Authorization"] = f"Bearer {new_token}"
        return super().send(request, **kwargs)

    def _refresh(self) -> str | None:
        tokens = load_tokens()
        if not tokens or not tokens.get("refresh"):
            return None

        self._refreshing = True
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/refresh",
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {tokens['refresh']}",  # ← refresh token as Bearer
                },
                timeout=10,
            )

            if resp.status_code != 200:
                clear_tokens()
                _notify_logout()
                return None

            data       = resp.json()
            new_access = data["access_token"]
            self.headers["Authorization"] = f"Bearer {new_access}"
            save_tokens(new_access, tokens["refresh"])
            return new_access

        except Exception:
            return None
        finally:
            self._refreshing = False


session = AutoRefreshSession()

_on_session_expired = None

def register_expiry_callback(fn):
    global _on_session_expired
    _on_session_expired = fn

def _notify_logout():
    if _on_session_expired:
        _on_session_expired()



def set_token(access_token: str):
    if access_token:
        session.headers["Authorization"] = f"Bearer {access_token}"
    else:
        session.headers.pop("Authorization", None)


def clear_token():
    session.headers.pop("Authorization", None)


def api(method: str, path: str, **kwargs) -> dict:
    url  = BASE_URL.rstrip("/") + path
    resp = session.request(method.upper(), url, timeout=10, **kwargs)
    resp.raise_for_status()
    return resp.json()


def upload(path: str, filepath: str) -> dict:
    url   = BASE_URL.rstrip("/") + path
    token = session.headers.get("Authorization")
    headers = {"Authorization": token} if token else {}

    with open(filepath, "rb") as fh:
        fname = os.path.basename(filepath)
        resp  = requests.post(
            url,
            files={"file": (fname, fh)},
            headers=headers,
            timeout=60,
        )

    # handle 401 manually for upload (uses raw requests.post not session)
    if resp.status_code == 401:
        new_token = session._refresh()
        if new_token:
            with open(filepath, "rb") as fh:
                resp = requests.post(
                    url,
                    files={"file": (fname, fh)},
                    headers={"Authorization": f"Bearer {new_token}"},
                    timeout=60,
                )

    resp.raise_for_status()
    return resp.json()