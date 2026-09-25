from pydantic import BaseModel, ConfigDict, Field


class AcademicClassCreate(BaseModel):
    department_id: int = Field(gt=0)

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    section: str = Field(
        min_length=1,
        max_length=10,
    )

    semester: int = Field(
        ge=1,
        le=8,
    )


class AcademicClassResponse(BaseModel):
    id: int
    department_id: int
    name: str
    section: str
    semester: int

    model_config = ConfigDict(from_attributes=True)