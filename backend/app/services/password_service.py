from sqlalchemy.orm import Session

from backend.app.core.security import (
    hash_password,
    verify_password,
)
from backend.app.models.user import User
from backend.app.schemas.password import PasswordChangeRequest


class IncorrectPasswordError(ValueError):
    pass


class PasswordReuseError(ValueError):
    pass


def change_password(
    db: Session,
    user: User,
    password_data: PasswordChangeRequest,
) -> None:

    # Verify the existing password.
    if not verify_password(
        password_data.current_password,
        user.password_hash,
    ):
        raise IncorrectPasswordError(
            "Current password is incorrect."
        )

    # Prevent reusing the current password.
    if verify_password(
        password_data.new_password,
        user.password_hash,
    ):
        raise PasswordReuseError(
            "New password must differ from current password."
        )

    # Hash the new password before storing it.
    new_password_hash = hash_password(
        password_data.new_password
    )

    user.password_hash = new_password_hash
    user.must_change_password = False

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise