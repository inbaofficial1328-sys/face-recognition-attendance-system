
from pydantic import BaseModel, ConfigDict, Field


class AttendanceSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: int = Field(gt=0)
    total_students: int = Field(ge=0)
    present: int = Field(ge=0)
    absent: int = Field(ge=0)
    od: int = Field(ge=0)
    late: int = Field(ge=0)
    unmarked: int = Field(ge=0)
    attendance_percentage: float = Field(ge=0, le=100)
