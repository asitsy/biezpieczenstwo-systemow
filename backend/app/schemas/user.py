from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None  # опционально если 2FA включена

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_2fa_enabled: bool

    class Config:
        from_attributes = True