from sqlalchemy import (
    JSON, Column, Integer, String, DateTime, Text,
    Float, ForeignKey, BigInteger, Boolean, Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Role(Base):
    """
    Named role (e.g. 'admin', 'analyst', 'viewer').
    Roles own a set of fine-grained Permission codes.
    """
    __tablename__ = "roles"
 
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String(256), default="")
 
    # relationships
    user_roles       = relationship("UserRole",       back_populates="role",
                                    cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role",
                                    cascade="all, delete-orphan")
 
    @property
    def permissions(self):
        return [rp.permission for rp in self.role_permissions]
 
 
class Permission(Base):
    """
    Atomic capability code.
 
    Example codes:
        logs:upload        logs:delete        logs:view_all
        analysis:run       analysis:view_own  analysis:view_all
        report:generate    report:export      report:sign
        alert:manage       model:deploy       admin:users
    """
    __tablename__ = "permissions"
 
    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String(256), default="")
 
    role_permissions = relationship("RolePermission", back_populates="permission",
                                    cascade="all, delete-orphan")
 
 
class UserRole(Base):
    """Many-to-many join: users ↔ roles."""
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)
 
    user_id = Column(Integer, ForeignKey("users.id",  ondelete="CASCADE"),
                     primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id",  ondelete="CASCADE"),
                     primary_key=True)
 
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
 
 
class RolePermission(Base):
    """Many-to-many join: roles ↔ permissions."""
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)
 
    role_id       = Column(Integer, ForeignKey("roles.id",       ondelete="CASCADE"),
                            primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"),
                            primary_key=True)
 
    role       = relationship("Role",       back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
 