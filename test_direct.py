#!/usr/bin/env python
import os
import sys

# Cambiar al directorio backend
os.chdir('/Users/sergiorodrigo/Documents/GitHub/srodrigo23/otb/web-app/backend')
sys.path.insert(0, '/Users/sergiorodrigo/Documents/GitHub/srodrigo23/otb/web-app/backend/src')

from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal

# Crear sesión
db = SessionLocal()

try:
    print("=== Obteniendo usuario ID 10 ===")
    user = crud.get_user(db, 10)
    if user:
        print(f"Usuario: {user.first_name} {user.last_name}")
        print(f"Email: {user.email}")
        print(f"Phone: {user.phone_number}, Type: {type(user.phone_number)}")

        print("\n=== Intentando actualizar usuario ===")
        update_data = schemas.UserUpdate(
            first_name="Jeffrey EDITADO",
            last_name="Wright Actualizado"
        )

        updated_user = crud.update_user(db, 10, update_data)
        print(f"Usuario actualizado: {updated_user.first_name} {updated_user.last_name}")

        print("\n=== Intentando convertir a schema User ===")
        user_schema = schemas.User.model_validate(updated_user)
        print(f"Schema: {user_schema}")
        print("¡TODO FUNCIONA!")

    else:
        print("Usuario no encontrado")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
