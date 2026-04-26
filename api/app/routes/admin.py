from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.config import Settings
from app.core.dependencies import require_permission
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role, Permission, UserRole, RolePermission
from app.schemas.user import UserOut, RoleOut

router = APIRouter(prefix="/admin", tags=["Admin"])
bearer = HTTPBearer()



@router.post("/users/{user_id}/roles/{role_id}", response_model=UserOut)
def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(404, "Role not found")

    already = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    ).first()
    if already:
        raise HTTPException(409, "User already has this role")

    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.commit()
    db.refresh(user)
    return user



@router.delete("/users/{user_id}/roles/{role_id}", response_model=UserOut)
def remove_role_from_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    assignment = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    ).first()
    if not assignment:
        raise HTTPException(404, "User does not have this role")

    db.delete(assignment)
    db.commit()
    db.refresh(user)
    return user



@router.post("/roles/{role_id}/permissions/{permission_id}", response_model=RoleOut)
def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(404, "Role not found")

    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(404, "Permission not found")

    already = db.query(RolePermission).filter(
        RolePermission.role_id       == role_id,
        RolePermission.permission_id == permission_id,
    ).first()
    if already:
        raise HTTPException(409, "Role already has this permission")

    db.add(RolePermission(role_id=role_id, permission_id=permission_id))
    db.commit()
    db.refresh(role)
    return role



@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=RoleOut)
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(404, "Role not found")

    assignment = db.query(RolePermission).filter(
        RolePermission.role_id       == role_id,
        RolePermission.permission_id == permission_id,
    ).first()
    if not assignment:
        raise HTTPException(404, "Role does not have this permission")

    db.delete(assignment)
    db.commit()
    db.refresh(role)
    return role



@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    return db.query(Role).all()



@router.get("/permissions", response_model=list[dict])
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    perms = db.query(Permission).all()
    return [{"id": p.id, "code": p.code, "description": p.description} for p in perms]




@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    return db.query(User).order_by(User.created_at.desc()).all()



@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user



@router.patch("/users/{user_id}/activate", response_model=UserOut)
def set_user_active(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin:users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current_user.id:
        raise HTTPException(400, "Cannot deactivate your own account")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user



class PasswordReset(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < Settings.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {Settings.PASSWORD_MIN_LENGTH} characters"
            )
        return v


@router.patch("/users/{user_id}/reset-password", response_model=UserOut)
def reset_user_password(
    user_id: int,
    data: PasswordReset,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("admin:users")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.hashed_pw = hash_password(data.new_password)
    db.commit()
    db.refresh(user)
    return user