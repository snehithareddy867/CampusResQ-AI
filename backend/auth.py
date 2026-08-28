"""JWT auth utilities."""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

JWT_SECRET = os.environ.get("JWT_SECRET", "dev_secret_change_me")
JWT_ALG = os.environ.get("JWT_ALG", "HS256")
JWT_EXP_HOURS = 24 * 7

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def current_user_ctx(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Missing token")
    return decode_token(creds.credentials)


def require_roles(*roles: str):
    async def _dep(ctx: dict = Depends(current_user_ctx)) -> dict:
        if ctx.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden: role not permitted")
        return ctx
    return _dep


def validate_password_strength(pwd: str) -> Optional[str]:
    if len(pwd) < 8:
        return "Password must be at least 8 characters"
    if not any(c.isupper() for c in pwd):
        return "Password must include an uppercase letter"
    if not any(c.islower() for c in pwd):
        return "Password must include a lowercase letter"
    if not any(c.isdigit() for c in pwd):
        return "Password must include a number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/`~" for c in pwd):
        return "Password must include a special character"
    return None
