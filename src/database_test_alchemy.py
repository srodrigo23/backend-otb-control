from sqlalchemy.orm import sessionmaker
import sqlalchemy
from models import Neighbor
import pandas as pd
from datetime import datetime

engine=sqlalchemy.create_engine(
  f'sqlite:///db_test.db'
  # f"postgresql://postgres:otbcentralizadoqwerty@db.vnuioejzhnwuokpzwnqn.supabase.co:5432/postgres"
  # f"postgresql://postgres.vnuioejzhnwuokpzwnqn:otbcentralizadoqwerty@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Leer el archivo CSV
df = pd.read_csv('data/vecinos.csv')

def parse_date(date_str):
  """Convierte fechas en formato DD/MM/YYYY a objeto date"""
  if pd.isna(date_str) or date_str == '':
    return None
  try:
    # Manejar fechas con años de 4 dígitos incorrectos (como 2967)
    parts = str(date_str).split('/')
    if len(parts) == 3:
      day, month, year = parts
      # Corregir años que obviamente son errores (ej: 2967 -> 1967)
      if len(year) == 4 and int(year) > 2025:
        year = '19' + year[2:]
      elif len(year) == 2:
        # Asumir que años de 2 dígitos >= 25 son 1900s, sino 2000s
        year = '19' + year if int(year) >= 25 else '20' + year
      return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").date()
  except:
    return None
  return None

# Iterar sobre cada fila del CSV
for index, row in df.iterrows():
  # Extraer nombres - dividir la columna "Nombres" por espacios
  nombres = str(row['Nombres']).strip() if pd.notna(row['Nombres']) else ''
  apellido_paterno = str(row['Apellido Paterno']).strip() if pd.notna(row['Apellido Paterno']) else ''
  apellido_materno = str(row['Apellido Materno']).strip() if pd.notna(row['Apellido Materno']) else ''

  # Combinar apellidos
  last_name = f"{apellido_paterno} {apellido_materno}".strip()

  # Separar primer y segundo nombre si hay espacios
  nombre_parts = nombres.split() if nombres else ['']
  first_name = nombre_parts[0] if len(nombre_parts) > 0 else ''
  second_name = ' '.join(nombre_parts[1:]) if len(nombre_parts) > 1 else ''

  db_n = Neighbor(
    first_name=first_name or apellido_paterno,  # Si no hay nombre, usar apellido
    second_name=second_name,
    last_name=last_name,
    ci=int(row['CI']) if pd.notna(row['CI']) else None,
    phone_number=int(row['Cel']) if pd.notna(row['Cel']) else None,
    email=None,  # No hay email en el CSV
    birth_day=parse_date(row['Fecha Nac']),
    meter_code=str(row['Cod. medidor']).strip() if pd.notna(row['Cod. medidor']) else None,
    section=str(row['Seccion']).strip() if pd.notna(row['Seccion']) else None
  )

  db.add(db_n)
  print(f"Agregado: {first_name} {last_name} - Sección: {db_n.section}")

# Confirmar todos los cambios
db.commit()
print(f"\nTotal de vecinos agregados: {len(df)}")
