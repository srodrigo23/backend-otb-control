from sqlalchemy.orm import sessionmaker
import sqlalchemy
from app.models.model import (
    Neighbor, NeighborMeter, Measure, MeterReading, DebtType
)
import pandas as pd
from datetime import datetime, timedelta
import random

# Configurar engine
engine = sqlalchemy.create_engine(
    f'sqlite:///db_test.db'
    # f"postgresql://postgres:otbcentralizadoqwerty@db.vnuioejzhnwuokpzwnqn.supabase.co:5432/postgres"
)

# Crear todas las tablas
from app.db.database import Base
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("=" * 60)
print("INICIANDO CARGA DE DATOS COMPLETA")
print("=" * 60)

def parse_date(date_str):
    """Convierte fechas en formato DD/MM/YYYY a objeto date"""
    if pd.isna(date_str) or date_str == '':
        return None
    try:
        parts = str(date_str).split('/')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 4 and int(year) > 2025:
                year = '19' + year[2:]
            elif len(year) == 2:
                year = '19' + year if int(year) >= 25 else '20' + year
            return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").date()
    except:
        return None
    return None

# 1. CARGAR VECINOS DESDE CSV
print("\n1. Cargando vecinos desde CSV...")
df = pd.read_csv('data/vecinos_of.csv')

neighbors_list = []
for index, row in df.iterrows():
    nombres = str(row['Nombres']).strip() if pd.notna(row['Nombres']) else ''
    apellido_paterno = str(row['Apellido Paterno']).strip() if pd.notna(row['Apellido Paterno']) else ''
    apellido_materno = str(row['Apellido Materno']).strip() if pd.notna(row['Apellido Materno']) else ''

    last_name = f"{apellido_paterno} {apellido_materno}".strip()
    nombre_parts = nombres.split() if nombres else ['']
    first_name = nombre_parts[0] if len(nombre_parts) > 0 else ''
    second_name = ' '.join(nombre_parts[1:]) if len(nombre_parts) > 1 else ''

    db_neighbor = Neighbor(
        first_name=first_name or apellido_paterno,
        second_name=second_name,
        last_name=last_name,
        ci=str(row['CI']).strip() if pd.notna(row['CI']) else None,
        phone_number=str(row['Cel']).strip() if pd.notna(row['Cel']) else None,
        email=None,
        birth_day=parse_date(row['Fecha Nac']),
        section=str(row['Seccion']).strip() if pd.notna(row['Seccion']) else None,
        is_active=True
    )
    db.add(db_neighbor)
    db.flush()  # Para obtener el ID

    # Crear medidor principal para este vecino
    meter_code = str(row['Cod. medidor']).strip() if pd.notna(row['Cod. medidor']) else f"M-{db_neighbor.id:03d}"
    db_meter = NeighborMeter(
        neighbor_id=db_neighbor.id,
        meter_code=meter_code,
        label="Medidor Principal",
        is_active=True,
        installation_date=datetime.now().date() - timedelta(days=random.randint(365, 1825))
    )
    db.add(db_meter)

    neighbors_list.append(db_neighbor)
    print(f"  ✓ Agregado: {first_name} {last_name} - Medidor: {meter_code}")

db.commit()
print(f"\n  Total vecinos agregados: {len(neighbors_list)}")

# 2. CREAR TIPOS DE DEUDA
print("\n2. Creando tipos de deuda...")
debt_types = [
    DebtType(name="Consumo de Agua", description="Cobro mensual por consumo de agua"),
    DebtType(name="Multa por Inasistencia", description="Multa por no asistir a reunión obligatoria"),
    DebtType(name="Mantenimiento", description="Cuota de mantenimiento de áreas comunes"),
    DebtType(name="Mora", description="Recargo por pago tardío"),
]

for dt in debt_types:
    db.add(dt)
    print(f"  ✓ Tipo de deuda: {dt.name}")

db.commit()

# 3. EXTRAER COLUMNAS DE LECTURA DEL CSV
print("\n3. Identificando columnas de lectura...")
# Buscar todas las columnas que empiezan con "LEC"
reading_columns = [col for col in df.columns if col.startswith('LEC')]
print(f"  ✓ Columnas de lectura encontradas: {len(reading_columns)}")
for col in reading_columns:
    print(f"    - {col}")

# Función para parsear fechas de las columnas de lectura
def parse_reading_date(col_name):
    """
    Parsea fechas del formato 'LEC. 05/01/25' a objeto date
    """
    try:
        # Eliminar 'LEC.' y espacios
        date_str = col_name.replace('LEC.', '').replace('LEC', '').strip()

        # Parsear fecha DD/MM/YY
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            # Convertir año de 2 dígitos a 4 dígitos
            if len(year) == 2:
                year = '20' + year if int(year) < 50 else '19' + year

            return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y").date()
    except Exception as e:
        print(f"    Error parseando fecha de columna '{col_name}': {e}")
        return None
    return None

# 4. CREAR MEDICIONES DE AGUA BASADAS EN LAS COLUMNAS
print("\n4. Creando jornadas de medición de agua...")
measures = []
measures_dict = {}  # Para mapear columna -> measure

for col in reading_columns:
    measure_date = parse_reading_date(col)
    if not measure_date:
        continue

    period = measure_date.strftime("%Y-%m")

    measure = Measure(
        measure_date=measure_date,
        period=period,
        reader_name=random.choice(["Juan Pérez", "María López", "Carlos Ruiz"]),
        status="completed",
        total_meters=len(neighbors_list),
        meters_read=0,  # Se actualizará después
        meters_pending=0,
        notes=f"Medición del {measure_date.strftime('%d/%m/%Y')}"
    )
    db.add(measure)
    db.flush()
    measures.append(measure)
    measures_dict[col] = measure
    print(f"  ✓ Medición: {measure_date.strftime('%d/%m/%Y')} ({period})")

db.commit()

# 5. CREAR LECTURAS DE MEDIDORES DESDE EL CSV
print("\n5. Creando lecturas de medidores desde CSV...")
reading_count = 0
meters_read_per_measure = {measure.id: 0 for measure in measures}

for index, row in df.iterrows():
    # Obtener el código del medidor
    meter_code = str(row['Cod. medidor']).strip() if pd.notna(row['Cod. medidor']) else None
    if not meter_code:
        continue

    # Buscar el medidor en la base de datos
    meter = db.query(NeighborMeter).filter(NeighborMeter.meter_code == meter_code).first()
    if not meter:
        continue

    # Crear lecturas para cada columna de lectura
    for col in reading_columns:
        if col not in measures_dict:
            continue

        measure = measures_dict[col]

        # Obtener el valor de la lectura
        reading_value = row[col]

        # Validar que sea un número válido
        try:
            current_reading = int(float(reading_value))
            if current_reading == 0:
                # Lectura 0 puede significar medidor sin lectura
                continue
        except (ValueError, TypeError):
            # No es un número válido, saltar
            continue

        # Crear la lectura
        reading = MeterReading(
            measure_id=measure.id,
            meter_id=meter.id,
            current_reading=current_reading,
            reading_date=measure.measure_date,
            status="normal",
            has_anomaly=False,
            notes=f"Lectura: {current_reading}"
        )
        db.add(reading)
        reading_count += 1
        meters_read_per_measure[measure.id] += 1

# Actualizar contadores de mediciones
for measure in measures:
    measure.meters_read = meters_read_per_measure[measure.id]
    measure.meters_pending = measure.total_meters - measure.meters_read

db.commit()
print(f"  ✓ Total lecturas creadas: {reading_count}")
for measure in measures:
    print(f"    - {measure.measure_date.strftime('%d/%m/%Y')}: {measure.meters_read} lecturas")


print("\n" + "=" * 60)
print("RESUMEN DE DATOS CARGADOS")
print("=" * 60)
print(f"Vecinos:                    {len(neighbors_list)}")
print(f"Medidores:                  {db.query(NeighborMeter).count()}")
print(f"Tipos de deuda:             {len(debt_types)}")
print(f"Jornadas de medición:       {len(measures)}")
print(f"Lecturas de medidores:      {reading_count}")
print("=" * 60)
print("CARGA COMPLETA FINALIZADA ✓")
print("=" * 60)

db.close()
