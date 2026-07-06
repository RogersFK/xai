
import os
from pathlib import Path
import shutil
import mimetypes
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.log_file import LogFile

BASE_DIR   = Path(__file__).parent.parent.parent  # services → app → api
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

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

    dest_dir = UPLOAD_DIR / str(user_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path_abs = dest_dir / file.filename

    with open(dest_path_abs, "wb") as f:
        shutil.copyfileobj(file.file, f)

    size = dest_path_abs.stat().st_size
    mime = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    source, fmt = EXT_META.get(ext, ("generic", "unknown"))
    
    dest_path_relative = Path("uploads") / str(user_id) / file.filename


    record = LogFile(
        user_id       = user_id,
        original_name = file.filename,
        stored_path   = str(dest_path_relative),
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