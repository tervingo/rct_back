from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from models.recipe import Recipe, RecipeCreate
from bson import ObjectId
from typing import List
import shutil
import os
from pathlib import Path
import uuid
from fastapi.staticfiles import StaticFiles
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm
from auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_user,
    fake_users_db,
    UserInDB,
    create_user,
    delete_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash
)
from database import get_database, verify_connection
from models.user import UserCreate
import logging

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://recetaria.netlify.app",  # Tu dominio en Netlify
        "https://recetoteca.netlify.app", # Tu dominio en Netlify
        "http://localhost:3000",  # Para desarrollo local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
# MONGODB_URL = "mongodb://localhost:27017"
MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.recetarium

# Configurar la ruta para las imágenes
IMAGES_DIR = Path("public/images/recipes")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Montar el directorio de imágenes
app.mount("/images", StaticFiles(directory="public/images"), name="images")

# Configuración de Cloudinary (añade esto después de la configuración de FastAPI)
load_dotenv()
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
)

@app.on_event("startup")
async def startup_db_client():
    await verify_connection()

@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Convertir el objeto Pydantic a diccionario y añadir logs
    user_data = user.model_dump()
    print("User data:", user_data)  # Log para depuración
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": user_data["username"],
        "is_admin": user_data["is_admin"]  # Usar el campo directamente
    }
    print("Token data:", token_data)  # Log para depuración
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/recipes/", response_model=Recipe)
async def create_recipe(recipe: RecipeCreate, current_user: User = Depends(get_current_user)):
    recipe_dict = recipe.dict()
    
    # Convertir el conjunto de tags en una lista
    if "tags" in recipe_dict:
        recipe_dict["tags"] = list(recipe_dict["tags"])
    
    # Añadir metadata
    recipe_dict["metadata"] = {
        "author": "unknown",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "rating": None,
        "reviews_count": 0
    }
    
    result = await db.recetas.insert_one(recipe_dict)
    created_recipe = await db.recetas.find_one({"_id": result.inserted_id})
    created_recipe["id"] = str(created_recipe.pop("_id"))
    return Recipe(**created_recipe)

@app.get("/recipes/", response_model=List[Recipe])
async def get_recipes():
    recipes = []
    async for recipe in db.recetas.find():
        recipe["id"] = str(recipe.pop("_id"))
        # Añadir metadata por defecto si no existe
        if "metadata" not in recipe:
            recipe["metadata"] = {
                "author": "unknown",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "rating": None,
                "reviews_count": 0
            }
        recipes.append(Recipe(**recipe))
    return recipes

@app.get("/recipes/{recipe_id}", response_model=Recipe)
async def get_recipe(recipe_id: str):
    recipe = await db.recetas.find_one({"_id": ObjectId(recipe_id)})
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe["id"] = str(recipe.pop("_id"))
    # Añadir metadata por defecto si no existe
    if "metadata" not in recipe:
        recipe["metadata"] = {
            "author": "unknown",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "rating": None,
            "reviews_count": 0
        }
    return Recipe(**recipe)

@app.put("/recipes/{recipe_id}", response_model=Recipe)
async def update_recipe(recipe_id: str, recipe: RecipeCreate, current_user: User = Depends(get_current_user)):
    # Convertir el modelo a diccionario
    recipe_dict = recipe.dict()
    
    # Convertir el conjunto de tags en una lista si existe
    if "tags" in recipe_dict and isinstance(recipe_dict["tags"], set):
        recipe_dict["tags"] = list(recipe_dict["tags"])
    
    # Obtener la receta existente para mantener los metadatos
    existing_recipe = await db.recetas.find_one({"_id": ObjectId(recipe_id)})
    if existing_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    # Mantener los metadatos existentes, solo actualizar updated_at
    metadata = existing_recipe.get("metadata", {
        "author": "unknown",
        "created_at": datetime.utcnow(),
        "rating": None,
        "reviews_count": 0
    })
    metadata["updated_at"] = datetime.utcnow()
    recipe_dict["metadata"] = metadata
    
    # Actualizar la receta
    result = await db.recetas.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$set": recipe_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found or not modified")
    
    # Obtener la receta actualizada
    updated_recipe = await db.recetas.find_one({"_id": ObjectId(recipe_id)})
    updated_recipe["id"] = str(updated_recipe.pop("_id"))
    return Recipe(**updated_recipe)

@app.delete("/recipes/{recipe_id}", response_model=dict)
async def delete_recipe(recipe_id: str, current_user: User = Depends(get_current_user)):
    result = await db.recetas.delete_one({"_id": ObjectId(recipe_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully"}

# Endpoint para obtener todas las etiquetas existentes
@app.get("/tags/", response_model=List[str])
async def get_tags():
    # Obtener todas las etiquetas únicas de todas las recetas
    tags = set()
    async for recipe in db.recetas.find():
        if "tags" in recipe:
            tags.update(recipe["tags"])
    return sorted(list(tags))

# Endpoint para eliminar una etiqueta
@app.delete("/tags/{tag}")
async def delete_tag(tag: str):
    # Eliminar la etiqueta de todas las recetas que la usan
    await db.recetas.update_many(
        {"tags": tag},
        {"$pull": {"tags": tag}}
    )
    return {"message": f"Etiqueta '{tag}' eliminada correctamente"}

@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Validar el tipo de archivo
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser una imagen"
            )
        
        contents = await file.read()
        
        # Subir a Cloudinary en la carpeta 'recipes'
        upload_result = cloudinary.uploader.upload(
            contents,
            folder="recipes",  # Todas las imágenes irán a la carpeta 'recipes'
            resource_type="auto",
            # Opciones adicionales para optimización
            transformation=[
                {
                    'width': 1200,  # Ancho máximo
                    'crop': 'limit'  # Mantiene la proporción
                }
            ],
            quality='auto:good',  # Optimización automática de calidad
            fetch_format='auto'  # Mejor formato según el navegador
        )
        
        return {"image_path": upload_result["secure_url"]}
    except Exception as e:
        print(f"Error uploading image: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de administración de usuarios
@app.post("/users/", response_model=User)
async def create_new_user(
    user: UserCreate,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return await create_user(user)

@app.delete("/users/{username}")
async def remove_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges"
        )
    return await delete_user(username)

# Script para crear el primer usuario admin
@app.post("/initial-setup")
async def initial_setup():
    db = get_database()  # Ya no necesita await
    
    # Verificar si ya existe un usuario admin
    admin_exists = await db["users"].find_one({"username": "admin"})
    if admin_exists:
        raise HTTPException(
            status_code=400,
            detail="Initial setup has already been performed"
        )
    
    # Crear usuario admin
    hashed_password = get_password_hash("adminpassword")
    new_admin = {
        "username": "admin",
        "hashed_password": hashed_password,
        "disabled": False,
        "is_admin": True
    }
    
    await db["users"].insert_one(new_admin)
    return {"message": "Admin user created successfully"}