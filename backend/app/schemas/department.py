from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    code: str = Field(
        min_length=2,
        max_length=20,
    )

    name: str = Field(
        min_length=3,
        max_length=150,
    )


class DepartmentResponse(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)