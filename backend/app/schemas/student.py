from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    login_id: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=150)

    academic_class_id: int = Field(gt=0)

    college_id: str = Field(min_length=2, max_length=50)
    registration_number: str = Field(
        min_length=2,
        max_length=50,
    )

    umis_number: str | None = Field(
        default=None,
        max_length=50,
    )

    date_of_birth: date | None = None

    blood_group: str | None = Field(
        default=None,
        max_length=10,
    )

    phone_number: str | None = Field(
        default=None,
        max_length=15,
    )


class StudentResponse(BaseModel):
    id: int
    user_id: int
    academic_class_id: int | None

    college_id: str
    registration_number: str
    umis_number: str | None

    department: str
    class_name: str
    semester: int

    date_of_birth: date | None
    blood_group: str | None
    phone_number: str | None

    model_config = ConfigDict(from_attributes=True)


class StudentRegistrationResponse(BaseModel):
    student: StudentResponse
    temporary_password: str
    message: str = (
        "Student registered successfully. "
        "Deliver the temporary password securely and "
        "require the student to change it at first login."
    )


class StudentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    academic_class_id: int | None = Field(
        default=None,
        gt=0,
    )

    date_of_birth: date | None = None

    blood_group: str | None = Field(
        default=None,
        max_length=10,
    )

    phone_number: str | None = Field(
        default=None,
        max_length=15,
    )