from pydantic import BaseModel, EmailStr

class EmailRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str