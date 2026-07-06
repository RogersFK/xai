from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User
from app.services.analysis_service import (
    run_analysis, get_analysis, list_analyses, format_analysis_out
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])
bearer = HTTPBearer()




@router.post("/run")
def run(
    log_id:       int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    if not current_user.has_permission("analysis:run"):
        raise HTTPException(403, "Permission denied — requires: analysis:run")
    analysis = run_analysis(db, log_id, current_user.id)
    return format_analysis_out(analysis, db)


@router.get("/history")
def history(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    see_all   = current_user.has_permission("analysis:view_all")
    analyses  = list_analyses(db, current_user.id, see_all)
    from app.models.log_file import LogFile
    result = []
    for a in analyses:
        lf = db.query(LogFile).filter(LogFile.id == a.log_file_id).first()
        result.append({
            "id":           a.id,
            "filename":     lf.original_name if lf else "unknown",
            "threat_score": a.threat_score,
            "severity":     a.severity,
            "status":       a.status,
            "created_at":   a.created_at,
        })
    return result


@router.get("/{analysis_id}")
def detail(
    analysis_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    analysis = get_analysis(db, analysis_id)
    if (analysis.user_id != current_user.id
            and not current_user.has_permission("analysis:view_all")):
        raise HTTPException(403, "Access denied")
    return format_analysis_out(analysis, db)