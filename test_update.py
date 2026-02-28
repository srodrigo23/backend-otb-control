import sys

from app.models import model
from services import crud
sys.path.insert(0, 'src')

from sqlalchemy.orm import Session
from app.schemas import schema
from app.db.database import SessionLocal, engine

# Crear la sesión
db = SessionLocal()

try:
    # Intentar obtener el usuario
    user = db.query(model.User).filter(model.User.id == 4).first()
    print(f"Usuario encontrado: {user}")
    print(f"first_name: {user.first_name}")
    print(f"second_name: {user.second_name}")
    print(f"last_name: {user.last_name}")
    print(f"ci: {user.ci}")
    print(f"phone_number: {user.phone_number}, type: {type(user.phone_number)}")
    print(f"email: {user.email}")

    # Intentar crear el schema
    print("\nIntentando convertir a schema User...")
    user_schema = schema.User.model_validate(user)
    print(f"Schema creado exitosamente: {user_schema}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
