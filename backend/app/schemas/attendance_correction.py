
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AttendanceStatus = Literal[
    "PRESENT",
    "ABSENT",
    "OD",
    "LATE",
]


class AttendanceCorrectionRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    status: AttendanceStatus

    reason: str = Field(
        min_length=5,
        max_length=500,
    )
