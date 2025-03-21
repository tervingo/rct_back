import motor.motor_asyncio
from os import getenv

# Obtener la URL de conexión de las variables de entorno o usar un valor por defecto
MONGODB_URL = getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = getenv("DATABASE_NAME", "recetarium")

# Crear el cliente de MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

def get_database():
    return database