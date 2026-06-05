from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings
from app.core.errors import AuthenticationError

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def make_api_key(settings: Settings) -> tuple[str, str]:
    secret = token_urlsafe(32)
    key = f"{settings.api_key_prefix}_{secret}"
    return key, key[:12]


def create_access_token(
    *, settings: Settings, user_id: str, organization_id: str, role: str
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "org": organization_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_minutes)).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.access_token_secret, algorithm="HS256")


def create_refresh_token(*, settings: Settings, user_id: str) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    jti = str(uuid4())
    expires_at = now + timedelta(days=settings.refresh_token_ttl_days)
    payload = {
        "sub": user_id,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.refresh_token_secret, algorithm="HS256")
    return token, jti, expires_at


def decode_access_token(settings: Settings, token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.access_token_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise AuthenticationError("Access token is invalid or expired.") from exc
    if payload.get("type") != "access":
        raise AuthenticationError("Access token is invalid.")
    return payload


def decode_refresh_token(settings: Settings, token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.refresh_token_secret, algorithms=["HS256"])
    except JWTError as exc:
        raise AuthenticationError("Refresh token is invalid or expired.") from exc
    if payload.get("type") != "refresh":
        raise AuthenticationError("Refresh token is invalid.")
    return payload
