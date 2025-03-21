from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    is_admin: bool = False
    disabled: Optional[bool] = False

class User(UserBase):
    pass

class UserInDB(UserBase):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False