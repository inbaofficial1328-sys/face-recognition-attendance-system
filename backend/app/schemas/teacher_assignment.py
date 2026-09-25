
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeacherAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    teacher_id: int = Field(gt=0)
    academic_class_id: int = Field(gt=0)


class TeacherAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    academic_class_id: int
    created_at: datetime
