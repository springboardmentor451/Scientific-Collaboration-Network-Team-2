from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str
    captcha_id: str
    captcha_answer: str


class CaptchaResponse(BaseModel):
    challenge_id: str
    question: str
    expires_in: int


class CaptchaVerifyRequest(BaseModel):
    challenge_id: str
    answer: str


class CaptchaStartRequest(BaseModel):
    challenge_id: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True