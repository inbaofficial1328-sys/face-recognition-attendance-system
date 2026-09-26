
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AttendanceSessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    academic_class_id: int = Field(gt=0)
    attendance_date: date
    period_number: int = Field(ge=1, le=10)


class AttendanceSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_class_id: int
    teacher_id: int
    attendance_date: date
    period_number: int
    status: str
    created_at: datetime
