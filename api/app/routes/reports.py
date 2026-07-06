# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
# from sqlalchemy.orm import Session
# from jose import JWTError

# from app.core.dependencies import get_current_user
# from app.db.session import get_db
# from app.core.security import decode_token
# from app.models.user import User
# from app.models.report import Report
# from app.schemas.report import ReportListItem, AppendNotesRequest
# from app.services.report_service import (
#     generate_report, get_report_detail,
#     list_reports, append_notes,
# )

# router = APIRouter(prefix="/reports", tags=["Reports"])
# bearer = HTTPBearer()




# @router.post("/generate/{analysis_id}")
# def generate(
#     analysis_id:  int,
#     db:           Session = Depends(get_db),
#     current_user: User    = Depends(get_current_user),
# ):
#     if not current_user.has_permission("report:generate"):
#         raise HTTPException(403, "Permission denied — requires: report:generate")
#     report = generate_report(db, analysis_id, current_user.id)
#     return get_report_detail(db, report.id)


# @router.get("/", response_model=list[ReportListItem])
# def list_all(
#     db:           Session = Depends(get_db),
#     current_user: User    = Depends(get_current_user),
# ):
#     see_all = current_user.has_permission("report:export")
#     return list_reports(db, current_user.id, see_all)


# @router.get("/{report_id}")
# def detail(
#     report_id:    int,
#     db:           Session = Depends(get_db),
#     current_user: User    = Depends(get_current_user),
# ):
#     report = db.query(Report).filter(Report.id == report_id).first()
#     if not report:
#         raise HTTPException(404, "Report not found")
#     if (report.created_by != current_user.id
#             and not current_user.has_permission("report:export")):
#         raise HTTPException(403, "Access denied")
#     return get_report_detail(db, report_id)


# @router.patch("/{report_id}/notes")
# def add_notes(
#     report_id:    int,
#     data:         AppendNotesRequest,
#     db:           Session = Depends(get_db),
#     current_user: User    = Depends(get_current_user),
# ):
#     return append_notes(db, report_id, data.notes, current_user.id)


# @router.patch("/{report_id}/sign")
# def sign_report(
#     report_id:    int,
#     db:           Session = Depends(get_db),
#     current_user: User    = Depends(get_current_user),
# ):
#     if not current_user.has_permission("report:sign"):
#         raise HTTPException(403, "Permission denied — requires: report:sign")
#     from datetime import datetime
#     report = db.query(Report).filter(Report.id == report_id).first()
#     if not report:
#         raise HTTPException(404, "Report not found")
#     report.status    = "signed"
#     report.signed_at = datetime.utcnow()
#     report.chain_of_custody = (
#         f"{report.chain_of_custody}\n"
#         f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}] "
#         f"Signed by {current_user.username}"
#     ).strip()
#     db.commit()
#     db.refresh(report)
#     return get_report_detail(db, report_id)



from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.report import Report
from app.schemas.report import ReportListItem, AppendNotesRequest
from app.services.report_service import (
    generate_report, get_report_detail,
    list_reports, append_notes, sign_report,
    generate_pdf_bytes, encrypt_pdf,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate/{analysis_id}")
def generate(
    analysis_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    if not current_user.has_permission("report:generate"):
        raise HTTPException(403, "Permission denied — requires: report:generate")
    report = generate_report(db, analysis_id, current_user.id)
    return get_report_detail(db, report.id)


@router.get("/", response_model=list[ReportListItem])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    see_all = current_user.has_permission("report:export")
    return list_reports(db, current_user.id, see_all)


@router.get("/{report_id}")
def detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    if (report.created_by != current_user.id
            and not current_user.has_permission("report:export")):
        raise HTTPException(403, "Access denied")
    return get_report_detail(db, report_id)


@router.patch("/{report_id}/notes")
def add_notes(
    report_id:    int,
    data:         AppendNotesRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    return append_notes(db, report_id, data.notes, current_user.id)


@router.patch("/{report_id}/sign")
def sign(
    report_id:    int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    if not current_user.has_permission("report:sign"):
        raise HTTPException(403, "Permission denied — requires: report:sign")

    result = sign_report(db, report_id, current_user.username)
    detail = get_report_detail(db, report_id)
    detail["hash"] = result["hash"]
    return detail


@router.get("/{report_id}/download")
def download_pdf(
    report_id:    int,
    encrypt:      bool    = True,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(404, "Report not found")
    if (report.created_by != current_user.id
            and not current_user.has_permission("report:export")):
        raise HTTPException(403, "Access denied")

    try:
        pdf_bytes = generate_pdf_bytes(report)
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {e}")

    if encrypt:
        payload, hex_key = encrypt_pdf(pdf_bytes)
        return Response(
            content=payload,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="report_{report_id}.xpdf"'
                ),
                "X-Decrypt-Key": hex_key,
                "X-Key-Algorithm": "AES-256-GCM",
                "Access-Control-Expose-Headers": "X-Decrypt-Key, X-Key-Algorithm",
            }
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="report_{report_id}.pdf"'
            ),
        }
    )