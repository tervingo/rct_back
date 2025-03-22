from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from bson import ObjectId
from database import get_database
from models.user import User, UserCreate, UserInDB
import logging

load_dotenv()

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set in environment")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Modelos
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# Base de datos de usuarios de prueba
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrator",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$BW4DBBcUWLDPqJF4qjIx5O2Ge0AVebglYwPF2TaQeV7B4uUZac9NG",  # "adminpassword"
        "disabled": False,
    }
}

# Utilidades
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(username: str):
    db = get_database()
    user_dict = await db.users.find_one({"username": username})
    if user_dict:
        return User(**user_dict)

async def authenticate_user(username: str, password: str):
    db = get_database()
    user_dict = await db["users"].find_one({"username": username})
    print("MongoDB user data:", user_dict)  # Log para depuración
    
    if not user_dict:
        return False
    if not verify_password(password, user_dict["hashed_password"]):
        return False
    
    # Crear el objeto UserInDB con los campos exactos
    user = UserInDB(
        username=user_dict["username"],
        is_admin=user_dict.get("is_admin", False),
        disabled=user_dict.get("disabled", False),
        hashed_password=user_dict["hashed_password"]
    )
    print("Created UserInDB object:", user.model_dump())  # Log para depuración
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = get_database()
    user_dict = await db["users"].find_one({"username": username})
    if user_dict is None:
        raise credentials_exception
    
    return UserInDB(
        username=user_dict["username"],
        hashed_password=user_dict["hashed_password"],
        is_admin=user_dict.get("is_admin", False),
        disabled=user_dict.get("disabled", False)
    )

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Endpoints para gestión de usuarios
async def create_user(user: UserCreate):
    db = get_database()
    # Verificar si el usuario ya existe
    if await db.users.find_one({"username": user.username}):
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    user_dict = user.dict()
    user_dict["password"] = get_password_hash(user.password)
    user_dict["created_at"] = datetime.utcnow()
    
    result = await db.users.insert_one(user_dict)
    user_dict["id"] = str(result.inserted_id)
    
    return User(**user_dict)

async def delete_user(username: str):
    db = get_database()
    result = await db.users.delete_one({"username": username})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}
