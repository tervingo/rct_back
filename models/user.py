from typing import Optional
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    username: str
    is_admin: bool = Field(default=False)
    disabled: bool = Field(default=False)

    class Config:
        from_attributes = True

class User(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = Field(default=False)