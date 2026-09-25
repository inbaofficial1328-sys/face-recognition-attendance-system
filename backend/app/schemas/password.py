from pydantic import BaseModel, Field, model_validator


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=128,
    )

    new_password: str = Field(
        min_length=12,
        max_length=128,
    )

    @model_validator(mode="after")
    def validate_password_change(self):
        if self.current_password == self.new_password:
            raise ValueError(
                "New password must differ from current password."
            )

        return self


class PasswordChangeResponse(BaseModel):
    message: str