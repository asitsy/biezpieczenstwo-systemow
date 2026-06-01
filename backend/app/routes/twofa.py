from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.core.audit import log_action
from pydantic import BaseModel
import pyotp

router = APIRouter(prefix="/2fa", tags=["Two-Factor Auth"])

class TOTPVerify(BaseModel):
    code: str

@router.post("/setup")
def setup_2fa(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.is_2fa_enabled:
        raise HTTPException(400, "2FA already enabled")

    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        current_user.email,
        issuer_name="SecureCloudDrive"
    )

    # Сохраняем секрет временно (до подтверждения)
    current_user.totp_secret = secret
    db.commit()

    return {
        "secret": secret,
        "qr_uri": uri,
        "message": "Scan QR code in Google Authenticator then confirm with /2fa/confirm"
    }

@router.post("/confirm")
def confirm_2fa(
    data: TOTPVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.totp_secret:
        raise HTTPException(400, "Run /2fa/setup first")

    if not pyotp.TOTP(current_user.totp_secret).verify(data.code):
        raise HTTPException(400, "Invalid code")

    current_user.is_2fa_enabled = True
    db.commit()
    log_action(db, "2fa_enabled", user_id=current_user.id)

    return {"message": "2FA enabled successfully"}

@router.post("/disable")
def disable_2fa(
    data: TOTPVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_2fa_enabled:
        raise HTTPException(400, "2FA is not enabled")

    if not pyotp.TOTP(current_user.totp_secret).verify(data.code):
        raise HTTPException(400, "Invalid code")

    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    db.commit()
    log_action(db, "2fa_disabled", user_id=current_user.id)

    return {"message": "2FA disabled"}