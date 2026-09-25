import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.core.security import decode_access_token
from backend.app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate the token and retrieve its database user."""

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise unauthorized

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise unauthorized

    # Verify that the token's role matches the current database role.
    if payload.get("role") != user.role:
        raise unauthorized

    return user

from collections.abc import Callable

def require_password_changed(
    current_user: User = Depends(get_current_user),
) -> User:
    """Block protected access until the initial password is changed."""

    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password change required before accessing this resource.",
        )

    return current_user

VALID_ROLES = frozenset({
    "ADMIN",
    "HOD",
    "TEACHER",
    "STUDENT",
})


def require_roles(
    *allowed_roles: str,
) -> Callable:
    """Restrict access to users with permitted roles."""

    if not allowed_roles:
        raise ValueError(
            "At least one permitted role is required."
        )

    if not set(allowed_roles).issubset(VALID_ROLES):
        raise ValueError(
            "An unsupported role was provided."
        )

    def role_checker(
    current_user: User = Depends(require_password_changed),
) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource",
            )

        return current_user

    return role_checker