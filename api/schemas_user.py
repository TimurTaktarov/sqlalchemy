from pydantic import Field, BaseModel, EmailStr


class BaseFields(BaseModel):
    email: EmailStr = Field(description='your email', examples=['example@ukr.net'])
    name: str = Field(description='Name of user', examples=['Mark Twen'], min_length=3, max_length=50)


class PasswordField(BaseModel):
    password: str = Field(description='your unique password', examples=['12345678'], min_length=8)


class RegisterUserRequest(PasswordField, BaseFields):
    pass


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: int
    token_type: str = 'Bearer'
