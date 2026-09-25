
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.schemas.staff import StaffCreate


class DuplicateStaffError(ValueError):
    pass


def register_staff(
    db: Session,
    staff_data: StaffCreate,
) -> tuple[User, str]:

    login_id = staff_data.login_id.strip()
    full_name = staff_data.full_name.strip()

    if len(login_id) < 3 or len(full_name) < 2:
        raise ValueError(
            "Login ID or full name is invalid."
        )

    existing_user = db.scalar(
        select(User).where(
            User.login_id == login_id
        )
    )

    if existing_user is not None:
        raise DuplicateStaffError(
            "Login ID already exists."
        )

    temporary_password = token_urlsafe(24)

    staff = User(
        login_id=login_id,
        full_name=full_name,
        password_hash=hash_password(
            temporary_password
        ),
        role=staff_data.role,
        is_active=True,
        must_change_password=True,
    )

    try:
        db.add(staff)
        db.commit()
        db.refresh(staff)

    except IntegrityError as exc:
        db.rollback()

        raise DuplicateStaffError(
            "Login ID already exists."
        ) from exc

    except Exception:
        db.rollback()
        raise

    return staff, temporary_password


def get_staff_accounts(db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(User.role.in_(["HOD", "TEACHER"]))
            .order_by(User.id)
        ).all()
    )


def set_staff_active_status(
    db: Session,
    staff_id: int,
    is_active: bool,
) -> User:
    staff = db.get(User, staff_id)

    if staff is None or staff.role not in ("HOD", "TEACHER"):
        raise LookupError("Staff account not found.")

    staff.is_active = is_active

    try:
        db.commit()
        db.refresh(staff)
    except Exception:
        db.rollback()
        raise

    return staff
