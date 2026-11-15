from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin2026"),
        "role": "admin",
        "name": "Mission Commander Admin",
    },
    "mission_control": {
        "username": "mission_control",
        "hashed_password": pwd_context.hash("control2026"),
        "role": "mission_control",
        "name": "Earth Flight Surgeon",
    },
    "crew": {
        "username": "crew",
        "hashed_password": pwd_context.hash("crew2026"),
        "role": "crew",
        "name": "Astronaut Crew Terminal",
    },
}

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    user = USERS_DB.get(request.username)
    if not user or not pwd_context.verify(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password (hint: admin/admin2026, mission_control/control2026, crew/crew2026)",
        )
    token = create_token({
        "sub": user["username"],
        "role": user["role"],
        "name": user["name"],
    })
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        name=user["name"],
    )
