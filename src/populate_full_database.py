from sqlalchemy.orm import sessionmaker
import sqlalchemy
from models import (
    Neighbor, NeighborMeter, Measure, MeterReading,
    Meet, Assistance, DebtType, DebtItem,
    CollectDebt, Payment, PaymentDetail
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
from database import Base
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
df = pd.read_csv('data/vecinos.csv')

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

# 3. CREAR MEDICIONES DE AGUA (3 meses)
print("\n3. Creando jornadas de medición de agua...")
measures = []
for i in range(3):
    measure_date = datetime.now().date() - timedelta(days=90 - (i * 30))
    period = measure_date.strftime("%Y-%m")

    measure = Measure(
        measure_date=measure_date,
        period=period,
        reader_name=random.choice(["Juan Pérez", "María López", "Carlos Ruiz"]),
        status="completed",
        total_meters=len(neighbors_list),
        meters_read=len(neighbors_list),
        meters_pending=0,
        notes=f"Medición completa del mes {period}"
    )
    db.add(measure)
    db.flush()
    measures.append(measure)
    print(f"  ✓ Medición: {period} - {measure.reader_name}")

db.commit()

# 4. CREAR LECTURAS DE MEDIDORES
print("\n4. Creando lecturas de medidores...")
reading_count = 0
for neighbor in neighbors_list:
    # Obtener el medidor del vecino
    meter = db.query(NeighborMeter).filter(NeighborMeter.neighbor_id == neighbor.id).first()
    if not meter:
        continue

    previous = random.randint(1000, 5000)  # Lectura inicial

    for measure in measures:
        consumption = random.randint(5, 50)  # Consumo entre 5 y 50 m³
        current = previous + consumption

        reading = MeterReading(
            measure_id=measure.id,
            meter_id=meter.id,
            current_reading=current,
            reading_date=measure.measure_date,
            status="normal",
            has_anomaly=random.choice([True, False]) if consumption > 40 else False,
            notes=f"Consumo: {consumption} m³"
        )
        db.add(reading)
        previous = current
        reading_count += 1

db.commit()
print(f"  ✓ Total lecturas creadas: {reading_count}")

# 5. CREAR REUNIONES
print("\n5. Creando reuniones...")
meetings = []
meet_types = ["ordinaria", "extraordinaria", "emergencia"]
for i in range(5):
    meet_date = datetime.now() - timedelta(days=random.randint(30, 180))
    meet = Meet(
        meet_date=meet_date,
        meet_type=random.choice(meet_types),
        title=f"Reunión {i+1} - Asuntos del barrio",
        description="Discusión de temas importantes de la comunidad",
        location="Casa comunal",
        start_time=meet_date,
        end_time=meet_date + timedelta(hours=2),
        status="completed",
        is_mandatory=random.choice([True, False]),
        total_neighbors=len(neighbors_list),
        organizer="Directiva OTB"
    )
    db.add(meet)
    db.flush()
    meetings.append(meet)
    print(f"  ✓ Reunión: {meet.title} - {meet.meet_type}")

db.commit()

# 6. CREAR ASISTENCIAS A REUNIONES
print("\n6. Registrando asistencias a reuniones...")
assistance_count = 0
for meet in meetings:
    present_count = 0
    on_time_count = 0

    for neighbor in neighbors_list:
        is_present = random.choice([True, False, True])  # 66% de asistencia
        is_on_time = random.choice([True, False, True]) if is_present else False

        assistance = Assistance(
            meet_id=meet.id,
            neighbor_id=neighbor.id,
            is_present=is_present,
            is_on_time=is_on_time,
            arrival_time=meet.start_time + timedelta(minutes=random.randint(0, 30)) if is_present else None,
            has_excuse=random.choice([True, False]) if not is_present else False,
            excuse_reason="Motivos laborales" if not is_present and random.choice([True, False]) else None
        )
        db.add(assistance)

        if is_present:
            present_count += 1
            if is_on_time:
                on_time_count += 1
        assistance_count += 1

    # Actualizar estadísticas de la reunión
    meet.total_present = present_count
    meet.total_absent = len(neighbors_list) - present_count
    meet.total_on_time = on_time_count

db.commit()
print(f"  ✓ Total asistencias registradas: {assistance_count}")

# 7. CREAR DEUDAS DE AGUA
print("\n7. Creando deudas por consumo de agua...")
debt_type_water = db.query(DebtType).filter(DebtType.name == "Consumo de Agua").first()
water_debt_count = 0

for neighbor in neighbors_list:
    meter = db.query(NeighborMeter).filter(NeighborMeter.neighbor_id == neighbor.id).first()
    if not meter:
        continue

    # Crear deudas por cada medición
    readings = db.query(MeterReading).join(NeighborMeter).filter(
        NeighborMeter.id == meter.id
    ).all()

    for reading in readings:
        # Calcular monto basado en consumo (simulado)
        consumption = reading.current_reading - 1000  # Simplificado
        amount = max(500, consumption * 3)  # Mínimo 5 Bs, luego 3 Bs/m³ (en centavos)

        # Algunos vecinos ya pagaron
        is_paid = random.choice([True, False, False])  # 33% ya pagó

        debt = DebtItem(
            neighbor_id=neighbor.id,
            debt_type_id=debt_type_water.id,
            meter_reading_id=reading.id,
            amount=amount,
            amount_paid=amount if is_paid else 0,
            balance=0 if is_paid else amount,
            reason=f"Consumo de agua - {reading.notes}",
            period=db.query(Measure).filter(Measure.id == reading.measure_id).first().period,
            issue_date=reading.reading_date.date(),
            due_date=reading.reading_date.date() + timedelta(days=30),
            status="paid" if is_paid else "pending",
            paid_date=reading.reading_date.date() + timedelta(days=random.randint(1, 15)) if is_paid else None
        )
        db.add(debt)
        water_debt_count += 1

db.commit()
print(f"  ✓ Total deudas de agua creadas: {water_debt_count}")

# 8. CREAR DEUDAS POR INASISTENCIA
print("\n8. Creando multas por inasistencia...")
debt_type_fine = db.query(DebtType).filter(DebtType.name == "Multa por Inasistencia").first()
fine_count = 0

for meet in meetings:
    if not meet.is_mandatory:
        continue

    absences = db.query(Assistance).filter(
        Assistance.meet_id == meet.id,
        Assistance.is_present == False,
        Assistance.has_excuse == False
    ).all()

    for absence in absences:
        fine_amount = 2000  # 20 Bs en centavos

        debt = DebtItem(
            neighbor_id=absence.neighbor_id,
            debt_type_id=debt_type_fine.id,
            assistance_id=absence.id,
            amount=fine_amount,
            amount_paid=0,
            balance=fine_amount,
            reason=f"Inasistencia a reunión: {meet.title}",
            period=meet.meet_date.strftime("%Y-%m"),
            issue_date=meet.meet_date.date(),
            due_date=meet.meet_date.date() + timedelta(days=15),
            status="pending"
        )
        db.add(debt)
        fine_count += 1

db.commit()
print(f"  ✓ Total multas por inasistencia: {fine_count}")

# 9. CREAR JORNADAS DE COBRO
print("\n9. Creando jornadas de cobro...")
collect_debts = []
for i in range(2):
    collect_date = datetime.now().date() - timedelta(days=60 - (i * 30))

    collect = CollectDebt(
        collect_date=collect_date,
        period=collect_date.strftime("%Y-%m"),
        collector_name=random.choice(["Pedro Mamani", "Rosa Quispe"]),
        location="Plaza principal",
        status="completed",
        start_time=datetime.combine(collect_date, datetime.min.time().replace(hour=9)),
        end_time=datetime.combine(collect_date, datetime.min.time().replace(hour=17))
    )
    db.add(collect)
    db.flush()
    collect_debts.append(collect)
    print(f"  ✓ Jornada de cobro: {collect.period} - {collect.collector_name}")

db.commit()

# 10. CREAR PAGOS
print("\n10. Creando pagos...")
payment_count = 0
total_paid_amount = 0

for collect in collect_debts:
    neighbors_to_pay = random.sample(neighbors_list, k=random.randint(20, 40))

    for neighbor in neighbors_to_pay:
        # Obtener deudas pendientes del vecino
        pending_debts = db.query(DebtItem).filter(
            DebtItem.neighbor_id == neighbor.id,
            DebtItem.status == "pending"
        ).limit(random.randint(1, 3)).all()

        if not pending_debts:
            continue

        # Calcular monto total a pagar
        total_payment = sum([debt.balance for debt in pending_debts])

        payment = Payment(
            neighbor_id=neighbor.id,
            collect_debt_id=collect.id,
            payment_date=collect.collect_date,
            total_amount=total_payment,
            payment_method=random.choice(["cash", "transfer", "qr"]),
            reference_number=f"REC-{payment_count+1:05d}",
            received_by=collect.collector_name
        )
        db.add(payment)
        db.flush()

        # Crear detalles de pago
        for debt in pending_debts:
            detail = PaymentDetail(
                payment_id=payment.id,
                debt_item_id=debt.id,
                amount_applied=debt.balance,
                previous_balance=debt.balance,
                new_balance=0
            )
            db.add(detail)

            # Actualizar deuda
            debt.amount_paid += debt.balance
            debt.balance = 0
            debt.status = "paid"
            debt.paid_date = collect.collect_date

        payment_count += 1
        total_paid_amount += total_payment

db.commit()
print(f"  ✓ Total pagos creados: {payment_count}")
print(f"  ✓ Monto total cobrado: {total_paid_amount/100:.2f} Bs")

# Actualizar estadísticas de jornadas de cobro
for collect in collect_debts:
    payments = db.query(Payment).filter(Payment.collect_debt_id == collect.id).all()
    collect.total_payments = len(payments)
    collect.total_collected = sum([p.total_amount for p in payments])
    collect.total_neighbors_paid = len(set([p.neighbor_id for p in payments]))

db.commit()

print("\n" + "=" * 60)
print("RESUMEN DE DATOS CARGADOS")
print("=" * 60)
print(f"Vecinos:                    {len(neighbors_list)}")
print(f"Medidores:                  {db.query(NeighborMeter).count()}")
print(f"Jornadas de medición:       {len(measures)}")
print(f"Lecturas de medidores:      {reading_count}")
print(f"Reuniones:                  {len(meetings)}")
print(f"Asistencias registradas:    {assistance_count}")
print(f"Tipos de deuda:             {len(debt_types)}")
print(f"Deudas de agua:             {water_debt_count}")
print(f"Multas por inasistencia:    {fine_count}")
print(f"Jornadas de cobro:          {len(collect_debts)}")
print(f"Pagos realizados:           {payment_count}")
print(f"Detalles de pago:           {db.query(PaymentDetail).count()}")
print("=" * 60)
print("CARGA COMPLETA FINALIZADA ✓")
print("=" * 60)

db.close()
