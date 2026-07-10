import base64
import hashlib
import hmac
import json
import re
import secrets
from datetime import UTC, datetime, timedelta

from app.config.base import get_settings

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 72


class PasswordPolicyError(ValueError):
    """Raised when a password does not satisfy the strength policy."""


def validate_password_strength(password: str) -> str:
    """Validate a plaintext password against the portal password policy.

    Returns the password unchanged when valid, otherwise raises
    ``PasswordPolicyError`` with a human-readable reason.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
        )
    if len(password) > PASSWORD_MAX_LENGTH:
        raise PasswordPolicyError(
            f"Password must be at most {PASSWORD_MAX_LENGTH} characters long"
        )
    if not re.search(r"[A-Za-z]", password):
        raise PasswordPolicyError("Password must contain at least one letter")
    if not re.search(r"\d", password):
        raise PasswordPolicyError("Password must contain at least one number")
    return password


def generate_random_password() -> str:
    """Return a cryptographically strong password for provider-managed accounts."""
    return secrets.token_urlsafe(48)


def generate_reset_token() -> str:
    """Return a high-entropy, URL-safe password-reset token."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Hash a reset token for at-rest storage (token itself is high-entropy)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_reset_token(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(hash_reset_token(token), token_hash)


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


def create_access_token(
    user_id: int,
    username: str,
    role: str,
    token_version: int = 0,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "ver": token_version,
        "iss": settings.auth_token_issuer,
        "aud": settings.auth_token_audience,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        "jti": secrets.token_urlsafe(16),
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
    now = int(datetime.now(UTC).timestamp())
    if int(payload.get("exp", 0)) < now:
        raise ValueError("Token expired")
    if int(payload.get("iat", 0)) > now + 60:
        raise ValueError("Token issued in the future")
    if payload.get("iss") != settings.auth_token_issuer:
        raise ValueError("Invalid token issuer")
    if payload.get("aud") != settings.auth_token_audience:
        raise ValueError("Invalid token audience")
    return payload
