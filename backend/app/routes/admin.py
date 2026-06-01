from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User, UserRole
from app.models.file import File
from app.models.audit_log import AuditLog
from app.schemas.user import UserResponse
from app.core.audit import log_action
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin Panel"])

class RoleUpdate(BaseModel):
    role: UserRole

class UserStats(BaseModel):
    total_users: int
    total_files: int
    total_logs: int

@router.get("/stats", response_model=UserStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return UserStats(
        total_users=db.query(User).count(),
        total_files=db.query(File).count(),
        total_logs=db.query(AuditLog).count()
    )

@router.get("/users", response_model=list[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return db.query(User).all()

@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    old_role = user.role
    user.role = data.role
    db.commit()

    log_action(db, "role_change", user_id=current_user.id,
               resource=user.email,
               details=f"{old_role} -> {data.role}")

    return {"message": f"Role updated to {data.role}"}

@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if user_id == current_user.id:
        raise HTTPException(400, "Cannot deactivate yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = False
    db.commit()

    log_action(db, "user_deactivated", user_id=current_user.id,
               resource=user.email)

    return {"message": f"User {user.email} deactivated"}

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    if user_id == current_user.id:
        raise HTTPException(400, "Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    log_action(db, "user_deleted", user_id=current_user.id,
               resource=user.email)

    db.delete(user)
    db.commit()

    return {"message": f"User {user.email} deleted"}