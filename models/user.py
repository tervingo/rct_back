from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    disabled: bool | None = None
    is_admin: bool = False

class User(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False