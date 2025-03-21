from typing import Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    username: str
    is_admin: bool = Field(default=False)
    disabled: Optional[bool] = Field(default=False)

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = Field(default=False)