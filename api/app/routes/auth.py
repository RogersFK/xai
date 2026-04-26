"""
app/routes/auth.py
──────────────────
POST /auth/register
POST /auth/login

DB logic lives here directly — no separate service needed for simple CRUD.
When auth grows (JWT, OAuth, email verification) extract to a service then.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UpdateProfileRequest, UserRegister, UserLogin, UserOut
from app.core.security import hash_password, verify_password

from app.core.security import create_access_token, create_refresh_token, decode_token
from jose import JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer = HTTPBearer()
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_pw):
        raise HTTPException(401, "Invalid username or password")
    
    if not user.is_active:
        raise HTTPException(403, "Account is disabled")
    return {
        "access_token":  create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type":    "bearer",
        "user":          UserOut.model_validate(user),
    }

@router.post("/refresh")
def refresh(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Not a refresh token")
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(401, "User not found")
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(401, "Not an access token")
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")
    return user



@router.patch("/me", response_model=UserOut)
def update_profile(
    body:        UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db:          Session = Depends(get_db),
):
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(401, "Not an access token")
        user = db.query(User).filter(
            User.id == int(payload["sub"])).first()
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

    if body.username:
        exists = db.query(User).filter(
            User.username == body.username,
            User.id != user.id
        ).first()
        if exists:
            raise HTTPException(409, "Username already taken.")
        user.username = body.username

    if body.email:
        exists = db.query(User).filter(
            User.email == body.email,
            User.id != user.id
        ).first()
        if exists:
            raise HTTPException(409, "Email already in use.")
        user.email = body.email

    db.commit()
    db.refresh(user)
    return user


@router.post("/me/change-password")
def change_password(
    body:        ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db:          Session = Depends(get_db),
):
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(401, "Not an access token")
        user = db.query(User).filter(
            User.id == int(payload["sub"])).first()
    except JWTError:
        raise HTTPException(401, "Invalid or expired token")

    if not verify_password(body.current_password, user.hashed_pw):
        raise HTTPException(400, "Current password is incorrect.")

    if len(body.new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")

    user.hashed_pw = hash_password(body.new_password)
    db.commit()
    return {"detail": "Password changed successfully."}


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username already taken")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")

    user = User(
        username  = data.username,
        email     = data.email,
        hashed_pw = hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
