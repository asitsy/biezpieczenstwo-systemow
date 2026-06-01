from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.audit_log import AuditLog
from app.models.user import User
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/logs", tags=["Audit Logs"])

class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    ip_address: str | None
    resource: str | None
    details: str | None
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=list[AuditLogResponse])
def get_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

@router.get("/my", response_model=list[AuditLogResponse])
def get_my_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.timestamp.desc()).limit(50).all()