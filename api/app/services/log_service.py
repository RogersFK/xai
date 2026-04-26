# """
# app/services/log_service.py
# ────────────────────────────
# Handles file upload persistence and retrieval.
# Physical files are stored under uploads/<user_id>/.
# """
# import uuid
# from pathlib import Path

# from fastapi import HTTPException, UploadFile
# from sqlalchemy.orm import Session

# from app.core.config import settings
# from app.models.log_file import LogFile


# def _user_upload_dir(user_id: int) -> Path:
#     p = settings.UPLOADS_DIR / str(user_id)
#     p.mkdir(parents=True, exist_ok=True)
#     return p


# def save_upload(db: Session, user_id: int, file: UploadFile) -> LogFile:
#     suffix = Path(file.filename).suffix.lower()
#     if suffix not in settings.ALLOWED_EXTENSIONS:
#         raise HTTPException(
#             400,
#             f"File type '{suffix}' not allowed. "
#             f"Allowed: {sorted(settings.ALLOWED_EXTENSIONS)}",
#         )

#     # Read & size-check
#     content = file.file.read()
#     size_mb = len(content) / (1024 * 1024)
#     if size_mb > settings.MAX_UPLOAD_MB:
#         raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")

#     # Store on disk with a UUID prefix to avoid name collisions
#     stored_name = f"{uuid.uuid4().hex}_{file.filename}"
#     dest = _user_upload_dir(user_id) / stored_name
#     dest.write_bytes(content)

#     record = LogFile(
#         user_id       = user_id,
#         original_name = file.filename,
#         stored_path   = str(dest),
#         file_size     = len(content),
#         mime_type     = file.content_type or "text/plain",
#     )
#     db.add(record)
#     db.commit()
#     db.refresh(record)
#     return record


# def list_files(db: Session, user_id: int) -> list[LogFile]:
#     return (
#         db.query(LogFile)
#         .filter(LogFile.user_id == user_id)
#         .order_by(LogFile.uploaded_at.desc())
#         .all()
#     )


# def get_file(db: Session, file_id: int, user_id: int) -> LogFile:
#     record = db.query(LogFile).filter(
#         LogFile.id == file_id,
#         LogFile.user_id == user_id,
#     ).first()
#     if not record:
#         raise HTTPException(404, "Log file not found")
#     return record


# def delete_file(db: Session, file_id: int, user_id: int) -> None:
#     record = get_file(db, file_id, user_id)
#     # Remove from disk
#     p = Path(record.stored_path)
#     if p.exists():
#         p.unlink()
#     db.delete(record)
#     db.commit()



import os
import shutil
import mimetypes
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.log_file import LogFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".log", ".csv", ".json", ".pcap", ".evtx", ".txt"}

# map extension → (log_source, log_format)
EXT_META = {
    ".log":  ("linux_syslog",   "syslog"),
    ".evtx": ("windows_event",  "evtx"),
    ".pcap": ("pcap",           "pcap"),
    ".csv":  ("firewall",       "csv"),
    ".json": ("generic",        "json"),
    ".txt":  ("generic",        "text"),
}


def save_upload(db: Session, user_id: int, file: UploadFile) -> LogFile:
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type '{ext}' is not supported")

    dest_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size      = os.path.getsize(dest_path)
    mime      = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    source, fmt = EXT_META.get(ext, ("generic", "unknown"))

    record = LogFile(
        user_id       = user_id,
        original_name = file.filename,
        stored_path   = dest_path,
        file_size     = size,
        mime_type     = mime,
        log_source    = source,
        log_format    = fmt,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_files(db: Session, user_id: int) -> list[LogFile]:
    return (
        db.query(LogFile)
        .filter(LogFile.user_id == user_id)
        .order_by(LogFile.uploaded_at.desc())
        .all()
    )


def delete_file(db: Session, file_id: int, user_id: int) -> None:
    lf = db.query(LogFile).filter(LogFile.id == file_id).first()
    if not lf:
        raise HTTPException(404, "Log file not found")

    if os.path.exists(lf.stored_path):
        os.remove(lf.stored_path)

    db.delete(lf)
    db.commit()