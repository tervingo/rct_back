from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from models.recipe import Recipe, RecipeCreate
from bson import ObjectId
from typing import List

app = FastAPI()

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL de tu frontend
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todas las cabeceras
)

# MongoDB connection
MONGODB_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGODB_URL)
db = client.recetarium

@app.post("/recipes/", response_model=Recipe)
async def create_recipe(recipe: RecipeCreate):
    recipe_dict = recipe.dict()
    
    # Add metadata
    metadata = {
        "author": "user123",  # En el futuro esto vendría del sistema de autenticación
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "rating": None,
        "reviews_count": 0
    }
    recipe_dict["metadata"] = metadata
    
    result = await db.recetas.insert_one(recipe_dict)
    recipe_dict["id"] = str(result.inserted_id)
    return Recipe(**recipe_dict)

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
async def update_recipe(recipe_id: str, recipe: RecipeCreate):
    # Obtener la receta existente para mantener los metadatos
    existing_recipe = await db.recetas.find_one({"_id": ObjectId(recipe_id)})
    if existing_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    recipe_dict = recipe.dict()
    
    # Mantener los metadatos existentes, solo actualizar updated_at
    metadata = existing_recipe.get("metadata", {
        "author": "unknown",
        "created_at": datetime.utcnow(),
        "rating": None,
        "reviews_count": 0
    })
    metadata["updated_at"] = datetime.utcnow()
    recipe_dict["metadata"] = metadata
    
    result = await db.recetas.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$set": recipe_dict}
    )
    
    updated_recipe = await db.recetas.find_one({"_id": ObjectId(recipe_id)})
    updated_recipe["id"] = str(updated_recipe.pop("_id"))
    return Recipe(**updated_recipe)

@app.delete("/recipes/{recipe_id}")
async def delete_recipe(recipe_id: str):
    result = await db.recetas.delete_one({"_id": ObjectId(recipe_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {"message": "Recipe deleted successfully"}