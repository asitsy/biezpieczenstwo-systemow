from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.user import User
from app.core.audit import log_action
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
import pyotp

router = APIRouter(prefix="/auth", tags=["Authentication"])

BLOCK_AFTER_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 15

@router.post("/register", response_model=UserResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password)
    )
    db.add(user)
    db.commit()
    log_action(db, "register", user_id=user.id, resource=user.email)
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(401, "Invalid credentials")

    # Проверка блокировки (brute-force)
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(429, f"Account locked. Try again later.")

    if not verify_password(data.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= BLOCK_AFTER_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=BLOCK_DURATION_MINUTES)
        db.commit()
        log_action(db, "failed_login", user_id=user.id, 
           ip_address=request.client.host, resource=user.email)
        raise HTTPException(401, "Invalid credentials")

    # Проверка 2FA если включена
    if user.is_2fa_enabled:
        if not data.totp_code:
            raise HTTPException(401, "2FA code required")
        if not pyotp.TOTP(user.totp_secret).verify(data.totp_code):
            raise HTTPException(401, "Invalid 2FA code")

    # Сброс счётчика неудачных попыток
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    log_action(db, "login", user_id=user.id, 
           ip_address=request.client.host, resource=user.email)

    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, role=user.role.value)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user