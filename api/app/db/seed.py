from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role, Permission, UserRole, RolePermission
from app.core.security import hash_password


PERMISSIONS = [
    ("logs:upload",      "Upload log files"),
    ("logs:view_own",    "View own log files"),
    ("logs:view_all",    "View all users log files"),
    ("logs:delete",      "Delete log files"),
    ("analysis:run",     "Run analysis on a log file"),
    ("analysis:view_own","View own analyses"),
    ("analysis:view_all","View all analyses"),
    ("report:generate",  "Generate a forensic report"),
    ("report:export",    "Export report to PDF / CSV"),
    ("report:sign",      "Digitally sign a report"),
    ("alert:manage",     "Acknowledge and resolve alerts"),
    ("model:deploy",     "Deploy a new ML model version"),
    ("admin:users",      "Manage users and roles"),
]

ROLES = {
    "admin": {
        "description": "Full system access",
        "permissions": [code for code, _ in PERMISSIONS],
    },
    "analyst": {
        "description": "Can upload, analyse, and report",
        "permissions": [
            "logs:upload", "logs:view_own", "logs:view_all",
            "analysis:run", "analysis:view_own", "analysis:view_all",
            "report:generate", "report:export",
            "alert:manage",
        ],
    },
    "viewer": {
        "description": "Read-only access to own data",
        "permissions": [
            "logs:view_own",
            "analysis:view_own",
            "report:export",
        ],
    },
}

ADMIN = {
    "username": "admin",
    "email":    "admin@system.local",
    "password": "admin@123",
    "role":     "admin",
}


def run_seed(db: Session) -> None:
    _seed_permissions(db)
    _seed_roles(db)
    _seed_admin(db)


def _seed_permissions(db: Session) -> None:
    for code, description in PERMISSIONS:
        exists = db.query(Permission).filter(Permission.code == code).first()
        if not exists:
            db.add(Permission(code=code, description=description))
    db.commit()


def _seed_roles(db: Session) -> None:
    for role_name, config in ROLES.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=config["description"])
            db.add(role)
            db.commit()
            db.refresh(role)

        existing_codes = {rp.permission.code for rp in role.role_permissions}

        for code in config["permissions"]:
            if code in existing_codes:
                continue
            perm = db.query(Permission).filter(Permission.code == code).first()
            if perm:
                db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()


def _seed_admin(db: Session) -> None:
    user = db.query(User).filter(User.username == ADMIN["username"]).first()
    if not user:
        user = User(
            username  = ADMIN["username"],
            email     = ADMIN["email"],
            hashed_pw = hash_password(ADMIN["password"]),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    admin_role = db.query(Role).filter(Role.name == ADMIN["role"]).first()
    already_assigned = db.query(UserRole).filter(
        UserRole.user_id == user.id,
        UserRole.role_id == admin_role.id,
    ).first()

    if not already_assigned:
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))
        db.commit()