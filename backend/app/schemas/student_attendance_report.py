
from pydantic import BaseModel, ConfigDict, Field


class StudentAttendanceReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: int = Field(gt=0)
    total_sessions: int = Field(ge=0)

    present: int = Field(ge=0)
    absent: int = Field(ge=0)
    od: int = Field(ge=0)
    late: int = Field(ge=0)
    unmarked: int = Field(ge=0)

    attendance_percentage: float = Field(
        ge=0,
        le=100,
    )


from pydantic import BaseModel, ConfigDict, Field


class StudentAttendanceReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: int = Field(gt=0)
    total_sessions: int = Field(ge=0)

    present: int = Field(ge=0)
    absent: int = Field(ge=0)
    od: int = Field(ge=0)
    late: int = Field(ge=0)
    unmarked: int = Field(ge=0)

    attendance_percentage: float = Field(
        ge=0,
        le=100,
    )
