"""
Migración: añade app_id="recetarium" a todas las recetas que no lo tengan.
Ejecutar una sola vez: python migrate_app_id.py
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL"))
    db = client[os.getenv("DATABASE_NAME", "recetarium")]

    result = await db.recetas.update_many(
        {"app_id": {"$exists": False}},
        {"$set": {"app_id": "recetarium"}}
    )
    print(f"Recetas migradas: {result.modified_count}")
    client.close()

if __name__ == "__main__":
    asyncio.run(migrate())
