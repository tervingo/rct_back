"""
Script para resetear la contraseña de usuarios administradores.
Uso: python reset_password.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "recetarium")


async def list_admins(db):
    admins = await db.users.find({"is_admin": True}).to_list(None)
    if admins:
        print("\nUsuarios administradores:")
        for u in admins:
            print(f"  - {u['username']}")
    else:
        print("\nNo se encontraron usuarios administradores en la base de datos.")
    return admins


async def reset_password(username: str, new_password: str):
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    result = await db.users.update_one(
        {"username": username},
        {"$set": {"hashed_password": hashed}}
    )

    if result.matched_count:
        print(f"Contraseña de '{username}' actualizada correctamente.")
    else:
        print(f"Usuario '{username}' no encontrado.")

    client.close()


async def main():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    admins = await list_admins(db)
    client.close()

    if not admins:
        return

    print()
    username = input("Introduce el nombre de usuario a resetear: ").strip()
    new_password = input("Introduce la nueva contraseña: ").strip()

    if not username or not new_password:
        print("Error: el usuario y la contraseña no pueden estar vacíos.")
        return

    await reset_password(username, new_password)


if __name__ == "__main__":
    asyncio.run(main())
