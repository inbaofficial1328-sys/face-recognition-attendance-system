from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.student_face import StudentFace
from backend.app.services import face_storage_service


@dataclass
class FaceRecoveryReport:
    orphan_file_student_ids: list[int] = field(
        default_factory=list
    )
    missing_file_student_ids: list[int] = field(
        default_factory=list
    )
    incomplete_enrollment_student_ids: list[int] = field(
        default_factory=list
    )
    temporary_files: list[str] = field(
        default_factory=list
    )


def scan_face_storage(
    db: Session,
    storage_dir: Path | None = None,
) -> FaceRecoveryReport:
    """Read-only scan of enrollment and storage consistency."""

    directory = (
        storage_dir
        if storage_dir is not None
        else face_storage_service.FACE_STORAGE_DIR
    )

    report = FaceRecoveryReport()

    records = db.scalars(
        select(StudentFace)
    ).all()

    records_by_student = {
        record.student_id: record
        for record in records
    }

    if directory.exists():
        for path in directory.iterdir():
            if not path.is_file():
                continue

            if path.name.endswith(".tmp"):
                report.temporary_files.append(path.name)
                continue

            if (
                not path.name.startswith("student_")
                or not path.name.endswith(".enc")
            ):
                continue

            identifier = path.name[
                len("student_"):-len(".enc")
            ]

            if not identifier.isdecimal():
                continue

            student_id = int(identifier)
            record = records_by_student.get(student_id)

            if record is None or not record.is_enrolled:
                report.orphan_file_student_ids.append(
                    student_id
                )

    for record in records:
        path = directory / (
            f"student_{record.student_id}.enc"
        )

        if record.is_enrolled and not path.is_file():
            report.missing_file_student_ids.append(
                record.student_id
            )

        if (
            not record.is_enrolled
            and record.enrolled_at is not None
        ):
            report.incomplete_enrollment_student_ids.append(
                record.student_id
            )

    report.orphan_file_student_ids.sort()
    report.missing_file_student_ids.sort()
    report.incomplete_enrollment_student_ids.sort()
    report.temporary_files.sort()

    return report
