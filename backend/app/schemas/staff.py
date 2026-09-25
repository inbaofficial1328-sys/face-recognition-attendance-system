
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StaffCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login_id: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=2, max_length=150)
    role: Literal["HOD", "TEACHER"]


class StaffResponse(BaseModel):
    id: int
    login_id: str
    full_name: str
    role: str
    is_active: bool
    must_change_password: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffRegistrationResponse(BaseModel):
    staff: StaffResponse
    temporary_password: str
    message: str = (
        "Staff account created successfully. "
        "Deliver the temporary password securely and "
        "require a password change at first login."
    )


class StaffStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool
