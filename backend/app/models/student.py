from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    college_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    umis_number: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    class_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    date_of_birth: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    blood_group: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
    )