"""
app/models/user.py
──────────────────
User table.  One user → many LogFiles and many Analyses (via LogFile).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    """
    Application user.  One user → many LogFiles and Analyses.
    Access control is done via Role → Permission codes.
    """
    __tablename__ = "users"
 
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(64),  unique=True, nullable=False, index=True)
    email      = Column(String(128), unique=True, nullable=False, index=True)
    hashed_pw  = Column(String,      nullable=False)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
 
    # relationships
    user_roles = relationship("UserRole",  back_populates="user",
                              cascade="all, delete-orphan")
    log_files  = relationship("LogFile",   back_populates="owner",
                              cascade="all, delete-orphan")
    analyses   = relationship("Analysis",  back_populates="user")
    audit_logs = relationship("AuditLog",  back_populates="user")
    alerts     = relationship("Alert",     back_populates="assigned_to",
                              foreign_keys="Alert.assigned_to_id")
 
    @property
    def roles(self):
        return [ur.role for ur in self.user_roles]
 
    def has_permission(self, code: str) -> bool:
        for role in self.roles:
            for perm in role.permissions:
                if perm.code == code:
                    return True
        return False