
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class StudentFace(Base):
    __tablename__ = "student_faces"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    is_enrolled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    consent_recorded: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    enrolled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
