from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True