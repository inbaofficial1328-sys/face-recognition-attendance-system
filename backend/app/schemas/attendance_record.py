
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AttendanceStatus = Literal[
    "PRESENT",
    "ABSENT",
    "OD",
    "LATE",
]


class AttendanceRecordCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: int = Field(gt=0)
    student_id: int = Field(gt=0)
    status: AttendanceStatus


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    student_id: int
    status: AttendanceStatus
    marked_by: str
    marked_at: datetime
