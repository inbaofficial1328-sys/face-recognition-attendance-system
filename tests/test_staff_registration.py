
import pytest

from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.security import verify_password
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.schemas.staff import StaffCreate
from backend.app.services.staff_service import (
    DuplicateStaffError,
    register_staff,
)


def test_staff_registration_security():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            staff_data = StaffCreate(
                login_id="test_teacher",
                full_name="Test Teacher",
                role="TEACHER",
            )

            staff, temporary_password = register_staff(
                db,
                staff_data,
            )

            assert staff.role == "TEACHER"
            assert staff.is_active is True
            assert staff.must_change_password is True

            assert staff.password_hash != temporary_password

            assert verify_password(
                temporary_password,
                staff.password_hash,
            )

            saved_staff = db.scalar(
                select(User).where(
                    User.login_id == "test_teacher"
                )
            )

            assert saved_staff is not None
            assert saved_staff.id == staff.id

            with pytest.raises(DuplicateStaffError):
                register_staff(db, staff_data)

            with pytest.raises(ValidationError):
                StaffCreate(
                    login_id="test_admin",
                    full_name="Test Administrator",
                    role="ADMIN",
                )

    finally:
        engine.dispose()
