from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime

class Ingredient(BaseModel):
    item: str
    amount: float
    unit: str

class Instruction(BaseModel):
    step: int
    text: str

class CookingTime(BaseModel):
    prep: int
    cook: int
    total: int

class Metadata(BaseModel):
    author: str
    created_at: datetime
    updated_at: datetime
    rating: Optional[float] = None
    reviews_count: Optional[int] = 0

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RecipeBase(BaseModel):
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    cooking_time: int
    servings: int
    category: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Champiñones al ajillo",
                    "description": "Champiñones al ajillo",
                    "ingredients": [
                        "Dos bandejas de champiñones",
                        "Dos dientes de ajo",
                        "Una pastilla de caldo de carne"
                    ],
                    "instructions": [
                        "Lavar los champiñones y quitarles el rabo",
                        "En una cazuela calentar el aceite de oliva"
                    ],
                    "cooking_time": 15,
                    "servings": 4,
                    "category": "Primero"
                }
            ]
        }
    }

class RecipeCreate(RecipeBase):
    pass

class Recipe(RecipeBase):
    id: str
    metadata: Metadata

    class Config:
        from_attributes = True
        populate_by_name = True