
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "student_id",
            name="uq_session_student_attendance",
        ),
        CheckConstraint(
            "status IN ('PRESENT', 'ABSENT', 'OD', 'LATE')",
            name="ck_attendance_status",
        ),
        CheckConstraint(
            "marked_by IN ('MANUAL', 'FACE_RECOGNITION')",
            name="ck_attendance_marking_method",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_sessions.id"),
        nullable=False,
        index=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    marked_by: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MANUAL",
    )

    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
