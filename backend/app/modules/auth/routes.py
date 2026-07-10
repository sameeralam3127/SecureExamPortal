from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.base import get_settings
from app.extensions.db import get_db
from app.models.user import AuthProvider, User, UserRole
from app.modules.auth.dependencies import get_current_user
from app.schemas.user import (
    GoogleLoginRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    StudentRegisterRequest,
    UserRead,
)
from app.services.job_queue import enqueue_password_reset_email
from app.utils.security import (
    create_access_token,
    generate_random_password,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
    verify_reset_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])

RESET_TOKEN_TTL_MINUTES = 30


def _issue_login(user: User) -> LoginResponse:
    return LoginResponse(
        access_token=create_access_token(
            user.id, user.username, user.role.value, user.token_version
        ),
        user=user,
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if user.auth_provider != AuthProvider.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google sign-in. Please continue with Google.",
        )

    return _issue_login(user)


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register_student(
    payload: StudentRegisterRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    duplicate = db.scalar(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    user = User(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.student,
        auth_provider=AuthProvider.password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_login(user)


@router.post("/google", response_model=LoginResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google auth is not configured",
        )

    try:
        response = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.credential},
            timeout=20,
        )
        response.raise_for_status()
        profile = response.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        ) from exc

    if profile.get("aud") != settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google client mismatch",
        )
    if profile.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token issuer",
        )
    if profile.get("email_verified") != "true":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified",
        )

    email = profile.get("email")
    full_name = profile.get("name") or "Google User"
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email not available",
        )
    email_domain = email.rsplit("@", 1)[-1].lower()
    allowed_domains = {domain.lower() for domain in settings.google_allowed_domains}
    if allowed_domains and email_domain not in allowed_domains:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google account domain is not allowed",
        )

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        base_username = email.split("@")[0].replace(".", "_")
        username = base_username
        suffix = 1
        while db.scalar(select(User).where(User.username == username)):
            suffix += 1
            username = f"{base_username}{suffix}"
        user = User(
            full_name=full_name,
            username=username,
            email=email,
            # Provider-managed account: store an unguessable random password so
            # the password-login path can never authenticate as this user.
            password_hash=hash_password(generate_random_password()),
            role=UserRole.student,
            auth_provider=AuthProvider.google,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return _issue_login(user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    # Bumping the token version invalidates every access token already issued
    # for this user (logout everywhere), since tokens are stateless.
    current_user.token_version += 1
    db.commit()
    return MessageResponse(detail="Signed out on all devices.")


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    generic = MessageResponse(
        detail="If an account exists for that email, a reset link has been sent."
    )
    user = db.scalar(select(User).where(User.email == payload.email))
    # Only password accounts can reset a password; do not reveal which case hit.
    if user is None or user.auth_provider != AuthProvider.password:
        return generic

    reset_token = generate_reset_token()
    user.reset_token_hash = hash_reset_token(reset_token)
    user.reset_token_expires_at = datetime.now(UTC) + timedelta(
        minutes=RESET_TOKEN_TTL_MINUTES
    )
    enqueue_password_reset_email(db, recipient_email=user.email, reset_token=reset_token)
    db.commit()
    return generic


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db),
) -> MessageResponse:
    token_hash = hash_reset_token(payload.token)
    user = db.scalar(select(User).where(User.reset_token_hash == token_hash))
    now = datetime.now(UTC)
    expires_at = user.reset_token_expires_at if user else None
    # Some backends (e.g. SQLite) return naive datetimes; treat them as UTC.
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if (
        user is None
        or user.reset_token_hash is None
        or expires_at is None
        or expires_at < now
        or not verify_reset_token(payload.token, user.reset_token_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link is invalid or has expired.",
        )

    user.password_hash = hash_password(payload.new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    # Revoke all existing sessions after a password change.
    user.token_version += 1
    db.commit()
    return MessageResponse(detail="Password updated. Please sign in with your new password.")


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
