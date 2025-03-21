from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class User(BaseModel):
    username: str
    disabled: bool | None = None
    is_admin: bool = False

class UserInDB(User):
    hashed_password: str

    class Config:
        from_attributes = True