from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from fastapi import HTTPException

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la URL de conexión de las variables de entorno
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "recetarium")

try:
    # Crear el cliente de MongoDB
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    
    # Verificar la conexión
    async def verify_connection():
        try:
            await client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Could not connect to MongoDB: {e}")
            raise HTTPException(status_code=500, detail="Database connection error")

except Exception as e:
    logger.error(f"Error initializing database connection: {e}")
    raise

def get_database():
    return database