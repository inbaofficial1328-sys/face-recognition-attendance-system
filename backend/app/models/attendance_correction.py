
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class AttendanceCorrection(Base):
    __tablename__ = "attendance_corrections"

    __table_args__ = (
        CheckConstraint(
            "old_status IN ('PRESENT', 'ABSENT', 'OD', 'LATE')",
            name="ck_correction_old_status",
        ),
        CheckConstraint(
            "new_status IN ('PRESENT', 'ABSENT', 'OD', 'LATE')",
            name="ck_correction_new_status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    attendance_record_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_records.id"),
        nullable=False,
        index=True,
    )

    corrected_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    old_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    new_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
