from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import (
    create_access_token,
    verify_password,
)
from backend.app.models.user import User


def authenticate_user(
    db: Session,
    login_id: str,
    password: str,
) -> User | None:
    """Validate user credentials against the database."""

    statement = select(User).where(
        User.login_id == login_id
    )

    user = db.scalar(statement)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def generate_login_token(user: User) -> dict:
    """Generate an access token for an authenticated user."""

    access_token = create_access_token(
        user_id=user.id,
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
    }