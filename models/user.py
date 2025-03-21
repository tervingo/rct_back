from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    username: str
    is_admin: bool = False
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False