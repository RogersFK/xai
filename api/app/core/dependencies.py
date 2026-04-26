# app/core/dependencies.py
from jose import JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User
from app.core.security import decode_token
from sqlalchemy.orm import Session
from app.db.session import get_db


bearer = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        return int(payload["sub"])
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(401, "Not an access token")
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(401, "User not found")
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    return user




def require_permission(code: str):
    def checker(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(code):
            raise HTTPException(403, f"Permission denied — requires: {code}")
        return current_user
    return checker    
    