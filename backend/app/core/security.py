from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.core.database import settings

# ── Argon2 ────────────────────────────────────────────────
ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64MB
    parallelism=2
)

def hash_password(plain: str) -> str:
    return ph.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False

# ── JWT ───────────────────────────────────────────────────
ALGORITHM = "HS256"

def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

# ── AES-256 (Fernet) ──────────────────────────────────────
cipher = Fernet(settings.FILE_ENCRYPTION_KEY.encode())

def encrypt_file(data: bytes) -> bytes:
    return cipher.encrypt(data)

def decrypt_file(encrypted: bytes) -> bytes:
    return cipher.decrypt(encrypted)