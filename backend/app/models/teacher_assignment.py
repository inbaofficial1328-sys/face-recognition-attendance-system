
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"

    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "academic_class_id",
            name="uq_teacher_class_assignment",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    academic_class_id: Mapped[int] = mapped_column(
        ForeignKey("academic_classes.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
