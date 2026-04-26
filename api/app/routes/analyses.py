# """
# app/routes/analyses.py
# ──────────────────────
# POST /analyses/run?user_id=<id>           — trigger AI analysis on a file
# GET  /analyses/?user_id=<id>             — all analyses for a user
# GET  /analyses/file/<file_id>?user_id=<id> — analyses for a specific file
# GET  /analyses/<id>?user_id=<id>         — single analysis detail
# """
# import random

# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session

# from app.models.log_file import LogFile
# from app.core.dependencies import get_current_user_id
# from app.db.session import get_db
# from app.schemas.log_analysis import AnalysisRequest, AnalysisOut
# from app.services.analysis_service import (
#     run_analysis,
#     list_analyses,
#     list_all_user_analyses,
#     get_analysis,
# )
# from app.services.log_service import get_file
# from pydantic import BaseModel


# router = APIRouter(prefix="/analyses", tags=["Analyses"])


# class AnalysisResult(BaseModel):
#     log_id:     int
#     filename:   str
#     status:     str          # "COMPLETE" | "FAILED"
#     threat_score: float      # 0.0 – 1.0
#     shap: list[dict]         # [{feature, value, max_val}]
#     events: list[dict]       # [{timestamp, event_id, score, status}]


# @router.post("/run", response_model=AnalysisResult)
# def run_analysis(
#     log_id: int,
#     user_id: int = Depends(get_current_user_id),
#     db: Session = Depends(get_db),
# ):
#     log = db.query(LogFile).filter(
#         LogFile.id == log_id,
#         LogFile.owner_id == user_id        # users can only scan own files
#     ).first()

#     if not log:
#         raise HTTPException(404, "Log file not found.")

#     # ── placeholder logic — replace with your ML pipeline ────────────
#     score = round(random.uniform(0.1, 0.95), 3)
#     result = AnalysisResult(
#         log_id=log.id,
#         filename=log.original_name,
#         status="COMPLETE",
#         threat_score=score,
#         shap=[
#             {"feature": "Source Entropy Variance",  "value":  0.428, "max_val": 0.5},
#             {"feature": "Packet Header Anomaly",    "value":  0.312, "max_val": 0.5},
#             {"feature": "Payload Signature Match",  "value": -0.115, "max_val": 0.5},
#             {"feature": "Temporal Drift",           "value":  0.098, "max_val": 0.5},
#         ],
#         events=[
#             {"timestamp": "2023-11-04 14:22:01", "event_id": "EFX-0012-92",
#              "score": int(score * 100), "status": "CRITICAL",
#              "lime": "High entropy payload detected.",
#              "pos": "Port 443 Tunneling [0.82]", "neg": "Known IP Range [-0.15]"},
#         ]
#     )
#     return result

# # COMMENTED FOR A WHILE
# # @router.post("/run", response_model=AnalysisOut, status_code=201)
# # def trigger_analysis(
# #     req: AnalysisRequest,
# #     user_id: int = Query(...),
# #     db: Session = Depends(get_db),
# # ):
# #     """Run AI analysis on a previously uploaded log file."""
# #     log_file = get_file(db, req.log_file_id, user_id)
# #     return run_analysis(db, log_file, req.user_prompt)


# @router.get("/", response_model=list[AnalysisOut])
# def all_analyses(user_id: int = Query(...), db: Session = Depends(get_db)):
#     """Return all analyses for a user across all their log files."""
#     return list_all_user_analyses(db, user_id)


# @router.get("/file/{file_id}", response_model=list[AnalysisOut])
# def file_analyses(
#     file_id: int,
#     user_id: int = Query(...),
#     db: Session = Depends(get_db),
# ):
#     """Return all analyses for a specific log file."""
#     return list_analyses(db, file_id, user_id)


# @router.get("/{analysis_id}", response_model=AnalysisOut)
# def single_analysis(
#     analysis_id: int,
#     user_id: int = Query(...),
#     db: Session = Depends(get_db),
# ):
#     """Return a single analysis record."""
#     return get_analysis(db, analysis_id, user_id)