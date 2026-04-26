from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.log_file import LogFile
from app.schemas.log_analysis import LogFileOut
from app.services.log_service import save_upload, list_files, delete_file

router = APIRouter(prefix="/logs", tags=["Log Files"])
bearer = HTTPBearer()





def _to_out(lf: LogFile) -> LogFileOut:
    return LogFileOut(
        id             = lf.id,
        user_id        = lf.user_id,
        original_name  = lf.original_name,
        file_size      = lf.file_size,
        mime_type      = lf.mime_type      or "",
        log_source     = lf.log_source     or "",
        log_format     = lf.log_format     or "",
        uploaded_at    = lf.uploaded_at,
        analysis_count = len(lf.analyses),
    )


@router.post("/upload", response_model=LogFileOut, status_code=201)
def upload_log(
    file:         UploadFile = File(...),
    db:           Session    = Depends(get_db),
    current_user: User       = Depends(get_current_user),
):
    if not current_user.has_permission("logs:upload"):
        raise HTTPException(403, "Permission denied — requires: logs:upload")
    record = save_upload(db, current_user.id, file)
    return _to_out(record)


@router.get("/", response_model=list[LogFileOut])
def get_files(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    # admins/analysts see all, viewers see only their own
    if current_user.has_permission("logs:view_all"):
        files = db.query(LogFile).order_by(LogFile.uploaded_at.desc()).all()
    else:
        files = list_files(db, current_user.id)
    return [_to_out(f) for f in files]


@router.get("/{file_id}", response_model=LogFileOut)
def get_file(
    file_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    lf = db.query(LogFile).filter(LogFile.id == file_id).first()
    if not lf:
        raise HTTPException(404, "Log file not found")
    if lf.user_id != current_user.id and not current_user.has_permission("logs:view_all"):
        raise HTTPException(403, "Access denied")
    return _to_out(lf)


@router.delete("/{file_id}", status_code=204)
def remove_file(
    file_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    lf = db.query(LogFile).filter(LogFile.id == file_id).first()
    if not lf:
        raise HTTPException(404, "Log file not found")
    if lf.user_id != current_user.id and not current_user.has_permission("logs:delete"):
        raise HTTPException(403, "Permission denied — requires: logs:delete")
    delete_file(db, file_id, current_user.id)