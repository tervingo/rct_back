import motor.motor_asyncio
from os import getenv
from fastapi import HTTPException
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Obtener la URL de conexión de las variables de entorno
MONGODB_URL = getenv("MONGODB_URL")
if not MONGODB_URL:
    raise ValueError("No MONGODB_URL environment variable set")

DATABASE_NAME = getenv("DATABASE_NAME", "recetarium")

try:
    # Crear el cliente de MongoDB
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=5000  # 5 segundos de timeout
    )
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