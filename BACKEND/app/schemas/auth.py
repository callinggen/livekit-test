from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str | None = None

class LoginRequest(BaseModel):
    identifier: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str | None = None
    phone_number: str | None = None

    class Config:
        from_attributes = True

class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyResetCodeRequest(BaseModel):
    email: str
    reset_code: str

class ResetPasswordRequest(BaseModel):
    email: str
    reset_code: str
    new_password: str
