from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def log_action(
    db: Session,
    action: str,
    user_id: int | None = None,
    ip_address: str | None = None,
    resource: str | None = None,
    details: str | None = None
):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        resource=resource,
        details=details
    )
    db.add(entry)
    db.commit()