import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from app.config.base import get_settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, expected_hash = password_hash.split("$", 1)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
    return hmac.compare_digest(digest.hex(), expected_hash)


def create_access_token(user_id: int, username: str, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": int(
            (
                datetime.now(timezone.utc)
                + timedelta(minutes=settings.access_token_expire_minutes)
            ).timestamp()
        ),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{body}.{signature}"


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Invalid token") from exc

    expected_signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid token")

    padded_body = body + "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded_body.encode("utf-8")).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token expired")
    return payload
