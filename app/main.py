from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from .services import crud
from .models import model
from .schemas import schema as schemas
from .db.database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

model.Base.metadata.create_all(bind=engine)

app = FastAPI()
# config for CORS
origins = [
    "http://localhost:5173",
    # "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
  db = SessionLocal()
  try:
      yield db
      
  finally:
      db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/neighbors/", response_model=schemas.Neighbor)
def create_neighbor(neighbor: schemas.NeighborCreate, db: Session = Depends(get_db)):
  # Validar email solo si se proporciona
  if neighbor.email:
    db_neighbor = crud.get_neighbor_by_email(db, email=neighbor.email)
    if db_neighbor:
      raise HTTPException(status_code=400, detail="Email already registered")
  return crud.create_neighbor(db=db, neighbor=neighbor)


@app.get("/neighbors/")
def read_neighbors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
  neighbors = crud.get_neighbors(db, skip=skip, limit=limit)
  if neighbors:
    return {
      "data": neighbors,
      "total": len(neighbors),
      "page": skip // limit + 1 if limit > 0 else 1,
      "size": limit
    }
  return {'success': 'True'}

# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#   db_user = crud.get_user(db, user_id=user_id)
#   if db_user is None:
#     raise HTTPException(status_code=404, detail="User not found")
#   return db_user


# @app.post("/users/{user_id}/items/", response_model=schemas.Item)
# def create_item_for_user(
#     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_item(db=db, item=item, user_id=user_id)


# @app.get("/items/", response_model=list[schemas.Item])
# def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = crud.get_items(db, skip=skip, limit=limit)
#     return items


@app.put("/neighbors/{neighbor_id}", response_model=schemas.Neighbor)
def update_neighbor(neighbor_id: int, neighbor: schemas.NeighborUpdate, db: Session = Depends(get_db)):
  db_neighbor = crud.update_neighbor(db, neighbor_id=neighbor_id, neighbor=neighbor)
  if db_neighbor is None:
    raise HTTPException(status_code=404, detail="Neighbor not found")
  return db_neighbor


@app.delete("/neighbors/{neighbor_id}")
def delete_neighbor(neighbor_id: int, db: Session = Depends(get_db)):
  success = crud.delete_neighbor(db, neighbor_id=neighbor_id)
  if not success:
    raise HTTPException(status_code=404, detail="Neighbor not found")
  return {"message": "Neighbor deleted successfully", "id": neighbor_id}


@app.get("/neighbors/{neighbor_id}/meters")
def get_neighbor_meters(neighbor_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todos los medidores de un vecino
  """
  # Verificar que el vecino existe
  neighbor = crud.get_neighbor(db, neighbor_id=neighbor_id)
  if neighbor is None:
    raise HTTPException(status_code=404, detail="Neighbor not found")

  # Obtener medidores
  meters = crud.get_neighbor_meters(db, neighbor_id=neighbor_id)

  # Formatear respuesta
  meters_data = []
  for meter in meters:
    meters_data.append({
      "id": meter.id,
      "meter_code": meter.meter_code,
      "label": meter.label,
      "is_active": meter.is_active,
      "installation_date": str(meter.installation_date) if meter.installation_date else None,
      "last_maintenance_date": str(meter.last_maintenance_date) if meter.last_maintenance_date else None,
      "notes": meter.notes,
      "created_at": str(meter.created_at)
    })

  return meters_data


@app.get("/neighbors/{neighbor_id}/payments")
def get_neighbor_payments(neighbor_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todos los pagos realizados por un vecino con sus detalles
  """
  # Verificar que el vecino existe
  neighbor = crud.get_neighbor(db, neighbor_id=neighbor_id)
  if neighbor is None:
    raise HTTPException(status_code=404, detail="Neighbor not found")

  # Obtener pagos
  payments = crud.get_neighbor_payments(db, neighbor_id=neighbor_id)

  # Formatear respuesta con detalles de cada pago
  payments_data = []
  for payment in payments:
    # Obtener detalles del pago (a qué deudas se aplicó)
    payment_details_list = []
    for detail in payment.payment_details:
      debt_item = detail.debt_item
      payment_details_list.append({
        "id": detail.id,
        "debt_item_id": detail.debt_item_id,
        "debt_reason": debt_item.reason if debt_item else "Desconocido",
        "debt_type_name": debt_item.debt_type.name if debt_item and debt_item.debt_type else "Desconocido",
        "amount_applied": detail.amount_applied,
        "previous_balance": detail.previous_balance,
        "new_balance": detail.new_balance,
        "notes": detail.notes
      })

    payments_data.append({
      "id": payment.id,
      "neighbor_id": payment.neighbor_id,
      "collect_debt_id": payment.collect_debt_id,
      "payment_date": str(payment.payment_date),
      "total_amount": payment.total_amount,
      "payment_method": payment.payment_method,
      "reference_number": payment.reference_number,
      "received_by": payment.received_by,
      "notes": payment.notes,
      "created_at": str(payment.created_at),
      "payment_details": payment_details_list
    })

  return payments_data


# ========== RUTAS DE DEUDAS ==========

@app.get("/neighbors/{neighbor_id}/debts/active", response_model=schemas.NeighborDebtsResponse)
def get_neighbor_active_debts(neighbor_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todas las deudas activas de un vecino (pending, partial, overdue)
  """
  # Verificar que el vecino existe
  neighbor = crud.get_neighbor(db, neighbor_id=neighbor_id)
  if neighbor is None:
    raise HTTPException(status_code=404, detail="Neighbor not found")

  # Obtener deudas activas
  debts = crud.get_neighbor_active_debts(db, neighbor_id=neighbor_id)

  # Formatear respuesta
  debt_details = []
  total_amount = 0
  total_balance = 0

  for debt in debts:
    # Obtener el nombre del tipo de deuda
    debt_type_name = debt.debt_type.name if debt.debt_type else "Desconocido"

    debt_detail = {
      "id": debt.id,
      "neighbor_id": debt.neighbor_id,
      "debt_type_id": debt.debt_type_id,
      "debt_type_name": debt_type_name,
      "meter_reading_id": debt.meter_reading_id,
      "assistance_id": debt.assistance_id,
      "amount": debt.amount,
      "amount_paid": debt.amount_paid,
      "balance": debt.balance,
      "reason": debt.reason,
      "period": debt.period,
      "issue_date": str(debt.issue_date),
      "due_date": str(debt.due_date) if debt.due_date else None,
      "paid_date": str(debt.paid_date) if debt.paid_date else None,
      "status": debt.status,
      "is_overdue": debt.is_overdue,
      "late_fee": debt.late_fee,
      "discount": debt.discount,
      "notes": debt.notes
    }
    debt_details.append(debt_detail)
    total_amount += debt.amount
    total_balance += debt.balance

  neighbor_name = f"{neighbor.first_name} {neighbor.second_name} {neighbor.last_name}".strip()

  return {
    "neighbor_id": neighbor_id,
    "neighbor_name": neighbor_name,
    "total_debts": len(debts),
    "total_amount": total_amount,
    "total_balance": total_balance,
    "debt_details": debt_details
  }


@app.get("/neighbors/{neighbor_id}/debts/all")
def get_neighbor_all_debts(neighbor_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todas las deudas de un vecino (incluyendo pagadas)
  """
  # Verificar que el vecino existe
  neighbor = crud.get_neighbor(db, neighbor_id=neighbor_id)
  if neighbor is None:
    raise HTTPException(status_code=404, detail="Neighbor not found")

  # Obtener todas las deudas
  debts = crud.get_neighbor_all_debts(db, neighbor_id=neighbor_id)

  # Formatear respuesta
  debt_details = []
  total_amount = 0
  total_balance = 0

  for debt in debts:
    debt_type_name = debt.debt_type.name if debt.debt_type else "Desconocido"

    debt_detail = {
      "id": debt.id,
      "neighbor_id": debt.neighbor_id,
      "debt_type_id": debt.debt_type_id,
      "debt_type_name": debt_type_name,
      "meter_reading_id": debt.meter_reading_id,
      "assistance_id": debt.assistance_id,
      "amount": debt.amount,
      "amount_paid": debt.amount_paid,
      "balance": debt.balance,
      "reason": debt.reason,
      "period": debt.period,
      "issue_date": str(debt.issue_date),
      "due_date": str(debt.due_date) if debt.due_date else None,
      "paid_date": str(debt.paid_date) if debt.paid_date else None,
      "status": debt.status,
      "is_overdue": debt.is_overdue,
      "late_fee": debt.late_fee,
      "discount": debt.discount,
      "notes": debt.notes
    }
    debt_details.append(debt_detail)
    total_amount += debt.amount
    total_balance += debt.balance

  neighbor_name = f"{neighbor.first_name} {neighbor.second_name} {neighbor.last_name}".strip()

  return {
    "neighbor_id": neighbor_id,
    "neighbor_name": neighbor_name,
    "total_debts": len(debts),
    "total_amount": total_amount,
    "total_balance": total_balance,
    "debt_details": debt_details
  }


@app.post("/debts/migrate-to-bolivianos")
def migrate_debts_to_bolivianos(db: Session = Depends(get_db)):
  """
  Convierte todas las deudas y pagos de centavos a bolivianos (divide por 100)
  IMPORTANTE: Ejecutar solo una vez para migrar datos existentes
  """
  # Migrar DebtItems
  debts = db.query(model.DebtItem).all()
  debts_updated = 0

  for debt in debts:
    # Convertir de centavos a bolivianos
    debt.amount = debt.amount / 100
    debt.amount_paid = debt.amount_paid / 100
    debt.balance = debt.balance / 100
    debt.late_fee = debt.late_fee / 100 if debt.late_fee else 0
    debt.discount = debt.discount / 100 if debt.discount else 0
    debts_updated += 1

  # Migrar Payments
  payments = db.query(model.Payment).all()
  payments_updated = 0

  for payment in payments:
    payment.total_amount = payment.total_amount / 100
    payments_updated += 1

  # Migrar PaymentDetails
  payment_details = db.query(model.PaymentDetail).all()
  details_updated = 0

  for detail in payment_details:
    detail.amount_applied = detail.amount_applied / 100
    if detail.previous_balance:
      detail.previous_balance = detail.previous_balance / 100
    if detail.new_balance:
      detail.new_balance = detail.new_balance / 100
    details_updated += 1

  # Migrar CollectDebts
  collect_debts = db.query(model.CollectDebt).all()
  collects_updated = 0

  for collect in collect_debts:
    collect.total_collected = collect.total_collected / 100
    collects_updated += 1

  db.commit()

  return {
    "message": "Successfully migrated all amounts from centavos to bolivianos",
    "debts_updated": debts_updated,
    "payments_updated": payments_updated,
    "payment_details_updated": details_updated,
    "collect_debts_updated": collects_updated
  }


@app.get("/debts/{debt_id}")
def get_debt_detail(debt_id: int, db: Session = Depends(get_db)):
  """
  Obtiene los detalles de una deuda específica
  """
  debt = crud.get_debt_item(db, debt_id=debt_id)
  if debt is None:
    raise HTTPException(status_code=404, detail="Debt not found")

  debt_type_name = debt.debt_type.name if debt.debt_type else "Desconocido"

  return {
    "id": debt.id,
    "neighbor_id": debt.neighbor_id,
    "debt_type_id": debt.debt_type_id,
    "debt_type_name": debt_type_name,
    "meter_reading_id": debt.meter_reading_id,
    "assistance_id": debt.assistance_id,
    "amount": debt.amount,
    "amount_paid": debt.amount_paid,
    "balance": debt.balance,
    "reason": debt.reason,
    "period": debt.period,
    "issue_date": str(debt.issue_date),
    "due_date": str(debt.due_date) if debt.due_date else None,
    "paid_date": str(debt.paid_date) if debt.paid_date else None,
    "status": debt.status,
    "is_overdue": debt.is_overdue,
    "late_fee": debt.late_fee,
    "discount": debt.discount,
    "notes": debt.notes,
    "created_at": str(debt.created_at),
    "updated_at": str(debt.updated_at)
  }


# ========== RUTAS DE MEDICIONES ==========

@app.get("/measures/")
def read_measures(db: Session = Depends(get_db)):
  """
  Obtiene todas las mediciones ordenadas por fecha de creación
  """
  measures = crud.get_measures(db)

  # Convertir las fechas a string para la respuesta
  measures_data = []
  for measure in measures:
    measures_data.append({
      "id": measure.id,
      "measure_date": str(measure.measure_date),
      "period": measure.period,
      "reader_name": measure.reader_name,
      "status": measure.status,
      "total_meters": measure.total_meters,
      "meters_read": measure.meters_read,
      "meters_pending": measure.meters_pending,
      "notes": measure.notes,
      "created_at": str(measure.created_at),
      "updated_at": str(measure.updated_at)
    })

  return measures_data


@app.get("/measures/{measure_id}", response_model=schemas.Measure)
def read_measure(measure_id: int, db: Session = Depends(get_db)):
  """
  Obtiene una medición específica
  """
  measure = crud.get_measure(db, measure_id=measure_id)
  if measure is None:
    raise HTTPException(status_code=404, detail="Measure not found")

  return {
    "id": measure.id,
    "measure_date": str(measure.measure_date),
    "period": measure.period,
    "reader_name": measure.reader_name,
    "status": measure.status,
    "total_meters": measure.total_meters,
    "meters_read": measure.meters_read,
    "meters_pending": measure.meters_pending,
    "notes": measure.notes,
    "created_at": str(measure.created_at),
    "updated_at": str(measure.updated_at)
  }


@app.post("/measures/", response_model=schemas.Measure)
def create_measure(measure: schemas.MeasureCreate, db: Session = Depends(get_db)):
  """
  Crea una nueva medición
  """
  db_measure = crud.create_measure(db=db, measure=measure)

  return {
    "id": db_measure.id,
    "measure_date": str(db_measure.measure_date),
    "period": db_measure.period,
    "reader_name": db_measure.reader_name,
    "status": db_measure.status,
    "total_meters": db_measure.total_meters,
    "meters_read": db_measure.meters_read,
    "meters_pending": db_measure.meters_pending,
    "notes": db_measure.notes,
    "created_at": str(db_measure.created_at),
    "updated_at": str(db_measure.updated_at)
  }


@app.put("/measures/{measure_id}", response_model=schemas.Measure)
def update_measure(measure_id: int, measure: schemas.MeasureUpdate, db: Session = Depends(get_db)):
  """
  Actualiza una medición existente
  """
  db_measure = crud.update_measure(db, measure_id=measure_id, measure=measure)
  if db_measure is None:
    raise HTTPException(status_code=404, detail="Measure not found")

  return {
    "id": db_measure.id,
    "measure_date": str(db_measure.measure_date),
    "period": db_measure.period,
    "reader_name": db_measure.reader_name,
    "status": db_measure.status,
    "total_meters": db_measure.total_meters,
    "meters_read": db_measure.meters_read,
    "meters_pending": db_measure.meters_pending,
    "notes": db_measure.notes,
    "created_at": str(db_measure.created_at),
    "updated_at": str(db_measure.updated_at)
  }


@app.delete("/measures/{measure_id}")
def delete_measure(measure_id: int, db: Session = Depends(get_db)):
  """
  Elimina una medición
  """
  success = crud.delete_measure(db, measure_id=measure_id)
  if not success:
    raise HTTPException(status_code=404, detail="Measure not found")
  return {"message": "Measure deleted successfully", "id": measure_id}


@app.get("/measures/{measure_id}/meter-readings")
def get_measure_meter_readings(measure_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todas las lecturas de medidores para una medición específica
  """
  # Verificar que la medición existe
  measure = crud.get_measure(db, measure_id=measure_id)
  if not measure:
    raise HTTPException(status_code=404, detail="Measure not found")

  # Obtener todas las lecturas de esta medición con información del vecino y medidor
  meter_readings = db.query(model.MeterReading).filter(
    model.MeterReading.measure_id == measure_id
  ).join(
    model.NeighborMeter, model.MeterReading.meter_id == model.NeighborMeter.id
  ).join(
    model.Neighbor, model.NeighborMeter.neighbor_id == model.Neighbor.id
  ).order_by(model.Neighbor.last_name, model.Neighbor.first_name).all()

  # Formatear respuesta con información del vecino
  readings_data = []
  for reading in meter_readings:
    neighbor = reading.meter.neighbor
    readings_data.append({
      "id": reading.id,
      "meter_id": reading.meter_id,
      "measure_id": reading.measure_id,
      "current_reading": reading.current_reading,
      "reading_date": str(reading.reading_date),
      "status": reading.status,
      "has_anomaly": reading.has_anomaly,
      "notes": reading.notes,
      "created_at": str(reading.created_at),
      "updated_at": str(reading.updated_at),
      # Información del vecino
      "neighbor_first_name": neighbor.first_name,
      "neighbor_second_name": neighbor.second_name,
      "neighbor_last_name": neighbor.last_name,
      "neighbor_ci": neighbor.ci,
      # Información del medidor
      "meter_number": reading.meter.meter_code,
    })

  return readings_data

@app.post("/measures/{measure_id}/generate-debts")
def generate_debts_from_measure(measure_id: int, db: Session = Depends(get_db)):
  """
  Genera deudas de consumo de agua para todos los vecinos basándose en las lecturas de una medición
  Lógica de cobro:
  - Consumo <= 20 m3: Bs. 20
  - Consumo > 20 m3: Bs. 1 por m3
  """
  # Verificar que la medición existe
  measure = crud.get_measure(db, measure_id=measure_id)
  if not measure:
    raise HTTPException(status_code=404, detail="Measure not found")

  # Obtener o crear el tipo de deuda "Consumo de Agua"
  debt_type = db.query(model.DebtType).filter(model.DebtType.name == "Consumo de Agua").first()
  if not debt_type:
    debt_type = model.DebtType(
      name="Consumo de Agua",
      description="Deuda por consumo de agua mensual"
    )
    db.add(debt_type)
    db.commit()
    db.refresh(debt_type)

  # Obtener todas las lecturas de esta medición
  meter_readings = db.query(model.MeterReading).filter(
    model.MeterReading.measure_id == measure_id
  ).join(
    model.NeighborMeter, model.MeterReading.meter_id == model.NeighborMeter.id
  ).all()

  debts_created = 0
  debts_skipped = 0
  debts_details = []

  for reading in meter_readings:
    # Verificar si ya existe una deuda para esta lectura
    existing_debt = db.query(model.DebtItem).filter(
      model.DebtItem.meter_reading_id == reading.id
    ).first()

    if existing_debt:
      debts_skipped += 1
      continue

    # Obtener la lectura anterior del mismo medidor
    previous_reading = db.query(model.MeterReading).filter(
      model.MeterReading.meter_id == reading.meter_id,
      model.MeterReading.id < reading.id
    ).order_by(model.MeterReading.id.desc()).first()

    # Calcular consumo
    if previous_reading:
      consumption = reading.current_reading - previous_reading.current_reading
    else:
      # Si no hay lectura anterior, usar la lectura actual como consumo
      consumption = reading.current_reading

    # Calcular monto según la lógica (en bolivianos)
    if consumption <= 20:
      amount = 20  # Bs. 20
    else:
      amount = consumption  # Bs. 1 por m3

    # Crear la deuda
    from datetime import date
    debt_item = model.DebtItem(
      neighbor_id=reading.meter.neighbor_id,
      debt_type_id=debt_type.id,
      meter_reading_id=reading.id,
      amount=amount,
      amount_paid=0,
      balance=amount,
      reason=f"Consumo de agua - {consumption} m3",
      period=measure.period,
      issue_date=date.today(),
      status="pending"
    )
    db.add(debt_item)
    debts_created += 1

    debts_details.append({
      "neighbor_id": reading.meter.neighbor_id,
      "neighbor_name": f"{reading.meter.neighbor.first_name} {reading.meter.neighbor.last_name}",
      "consumption": consumption,
      "amount": amount,
      "meter_reading_id": reading.id
    })

  db.commit()

  return {
    "message": f"Debts generated successfully",
    "debts_created": debts_created,
    "debts_skipped": debts_skipped,
    "total_readings": len(meter_readings),
    "details": debts_details
  }


@app.delete("/measures/{measure_id}/debts")
def delete_measure_debts(measure_id: int, db: Session = Depends(get_db)):
  """
  Elimina todas las deudas generadas para una medición específica
  Solo elimina deudas que no hayan sido pagadas (status = pending)
  """
  # Verificar que la medición existe
  measure = crud.get_measure(db, measure_id=measure_id)
  if not measure:
    raise HTTPException(status_code=404, detail="Measure not found")

  # Obtener todas las lecturas de esta medición
  meter_readings = db.query(model.MeterReading).filter(
    model.MeterReading.measure_id == measure_id
  ).all()

  reading_ids = [reading.id for reading in meter_readings]

  # Eliminar solo las deudas pendientes (no pagadas) asociadas a estas lecturas
  debts_deleted = db.query(model.DebtItem).filter(
    model.DebtItem.meter_reading_id.in_(reading_ids),
    model.DebtItem.status == "pending"
  ).delete(synchronize_session=False)

  db.commit()

  return {
    "message": f"Debts deleted successfully",
    "debts_deleted": debts_deleted
  }


# ========== RUTAS DE REUNIONES ==========

@app.get("/meets/")
def read_meets(db: Session = Depends(get_db)):
  """
  Obtiene todas las reuniones ordenadas por fecha de creación
  """
  meets = crud.get_meets(db)

  # Convertir las fechas a string para la respuesta
  meets_data = []
  for meet in meets:
    meets_data.append({
      "id": meet.id,
      "meet_date": str(meet.meet_date),
      "meet_type": meet.meet_type,
      "title": meet.title,
      "description": meet.description,
      "location": meet.location,
      "start_time": str(meet.start_time) if meet.start_time else None,
      "end_time": str(meet.end_time) if meet.end_time else None,
      "status": meet.status,
      "is_mandatory": meet.is_mandatory,
      "total_neighbors": meet.total_neighbors,
      "total_present": meet.total_present,
      "total_absent": meet.total_absent,
      "total_on_time": meet.total_on_time,
      "organizer": meet.organizer,
      "notes": meet.notes,
      "created_at": str(meet.created_at),
      "updated_at": str(meet.updated_at)
    })

  return meets_data


@app.get("/meets/{meet_id}", response_model=schemas.Meet)
def read_meet(meet_id: int, db: Session = Depends(get_db)):
  """
  Obtiene una reunión específica
  """
  meet = crud.get_meet(db, meet_id=meet_id)
  if meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  return {
    "id": meet.id,
    "meet_date": str(meet.meet_date),
    "meet_type": meet.meet_type,
    "title": meet.title,
    "description": meet.description,
    "location": meet.location,
    "start_time": str(meet.start_time) if meet.start_time else None,
    "end_time": str(meet.end_time) if meet.end_time else None,
    "status": meet.status,
    "is_mandatory": meet.is_mandatory,
    "total_neighbors": meet.total_neighbors,
    "total_present": meet.total_present,
    "total_absent": meet.total_absent,
    "total_on_time": meet.total_on_time,
    "organizer": meet.organizer,
    "notes": meet.notes,
    "created_at": str(meet.created_at),
    "updated_at": str(meet.updated_at)
  }


@app.post("/meets/", response_model=schemas.Meet)
def create_meet(meet: schemas.MeetCreate, db: Session = Depends(get_db)):
  """
  Crea una nueva reunión
  """
  db_meet = crud.create_meet(db=db, meet=meet)

  return {
    "id": db_meet.id,
    "meet_date": str(db_meet.meet_date),
    "meet_type": db_meet.meet_type,
    "title": db_meet.title,
    "description": db_meet.description,
    "location": db_meet.location,
    "start_time": str(db_meet.start_time) if db_meet.start_time else None,
    "end_time": str(db_meet.end_time) if db_meet.end_time else None,
    "status": db_meet.status,
    "is_mandatory": db_meet.is_mandatory,
    "total_neighbors": db_meet.total_neighbors,
    "total_present": db_meet.total_present,
    "total_absent": db_meet.total_absent,
    "total_on_time": db_meet.total_on_time,
    "organizer": db_meet.organizer,
    "notes": db_meet.notes,
    "created_at": str(db_meet.created_at),
    "updated_at": str(db_meet.updated_at)
  }


@app.put("/meets/{meet_id}", response_model=schemas.Meet)
def update_meet(meet_id: int, meet: schemas.MeetUpdate, db: Session = Depends(get_db)):
  """
  Actualiza una reunión existente
  """
  db_meet = crud.update_meet(db, meet_id=meet_id, meet=meet)
  if db_meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  return {
    "id": db_meet.id,
    "meet_date": str(db_meet.meet_date),
    "meet_type": db_meet.meet_type,
    "title": db_meet.title,
    "description": db_meet.description,
    "location": db_meet.location,
    "start_time": str(db_meet.start_time) if db_meet.start_time else None,
    "end_time": str(db_meet.end_time) if db_meet.end_time else None,
    "status": db_meet.status,
    "is_mandatory": db_meet.is_mandatory,
    "total_neighbors": db_meet.total_neighbors,
    "total_present": db_meet.total_present,
    "total_absent": db_meet.total_absent,
    "total_on_time": db_meet.total_on_time,
    "organizer": db_meet.organizer,
    "notes": db_meet.notes,
    "created_at": str(db_meet.created_at),
    "updated_at": str(db_meet.updated_at)
  }


@app.delete("/meets/{meet_id}")
def delete_meet(meet_id: int, db: Session = Depends(get_db)):
  """
  Elimina una reunión
  """
  success = crud.delete_meet(db, meet_id=meet_id)
  if not success:
    raise HTTPException(status_code=404, detail="Meet not found")
  return {"message": "Meet deleted successfully", "id": meet_id}


@app.get("/meets/{meet_id}/assistances")
def read_meet_assistances(meet_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todas las asistencias de una reunión específica
  """
  # Verificar que la reunión existe
  meet = crud.get_meet(db, meet_id=meet_id)
  if meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  assistances = crud.get_meet_assistances(db, meet_id=meet_id)

  # Formatear respuesta con datos del vecino
  assistances_data = []
  for assistance in assistances:
    neighbor = assistance.neighbor
    neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

    assistances_data.append({
      "id": assistance.id,
      "meet_id": assistance.meet_id,
      "neighbor_id": assistance.neighbor_id,
      "neighbor_name": neighbor_name,
      "is_present": assistance.is_present,
      "is_on_time": assistance.is_on_time,
      "arrival_time": str(assistance.arrival_time) if assistance.arrival_time else None,
      "departure_time": str(assistance.departure_time) if assistance.departure_time else None,
      "excuse_reason": assistance.excuse_reason,
      "has_excuse": assistance.has_excuse,
      "represented_by": assistance.represented_by,
      "has_representative": assistance.has_representative,
      "notes": assistance.notes
    })

  return assistances_data


@app.post("/meets/{meet_id}/assistances", response_model=schemas.Assistance)
def create_meet_assistance(meet_id: int, assistance: schemas.AssistanceBase, db: Session = Depends(get_db)):
  """
  Crea un registro de asistencia para una reunión
  """
  # Verificar que la reunión existe
  meet = crud.get_meet(db, meet_id=meet_id)
  if meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  # Crear el schema con meet_id
  assistance_create = schemas.AssistanceCreate(
    meet_id=meet_id,
    neighbor_id=assistance.neighbor_id,
    is_present=assistance.is_present,
    is_on_time=assistance.is_on_time
  )

  db_assistance = crud.create_assistance(db=db, assistance=assistance_create)

  # Obtener nombre del vecino para la respuesta
  neighbor = db_assistance.neighbor
  neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

  return {
    "id": db_assistance.id,
    "meet_id": db_assistance.meet_id,
    "neighbor_id": db_assistance.neighbor_id,
    "neighbor_name": neighbor_name,
    "is_present": db_assistance.is_present,
    "is_on_time": db_assistance.is_on_time,
    "arrival_time": str(db_assistance.arrival_time) if db_assistance.arrival_time else None,
    "departure_time": str(db_assistance.departure_time) if db_assistance.departure_time else None,
    "excuse_reason": db_assistance.excuse_reason,
    "has_excuse": db_assistance.has_excuse,
    "represented_by": db_assistance.represented_by,
    "has_representative": db_assistance.has_representative,
    "notes": db_assistance.notes
  }


@app.put("/assistances/{assistance_id}", response_model=schemas.Assistance)
def update_assistance(assistance_id: int, assistance: schemas.AssistanceUpdate, db: Session = Depends(get_db)):
  """
  Actualiza un registro de asistencia
  """
  db_assistance = crud.update_assistance(db, assistance_id=assistance_id, assistance=assistance)
  if db_assistance is None:
    raise HTTPException(status_code=404, detail="Assistance not found")

  # Obtener nombre del vecino para la respuesta
  neighbor = db_assistance.neighbor
  neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

  return {
    "id": db_assistance.id,
    "meet_id": db_assistance.meet_id,
    "neighbor_id": db_assistance.neighbor_id,
    "neighbor_name": neighbor_name,
    "is_present": db_assistance.is_present,
    "is_on_time": db_assistance.is_on_time,
    "arrival_time": str(db_assistance.arrival_time) if db_assistance.arrival_time else None,
    "departure_time": str(db_assistance.departure_time) if db_assistance.departure_time else None,
    "excuse_reason": db_assistance.excuse_reason,
    "has_excuse": db_assistance.has_excuse,
    "represented_by": db_assistance.represented_by,
    "has_representative": db_assistance.has_representative,
    "notes": db_assistance.notes
  }


@app.post("/meets/{meet_id}/recalculate-statistics")
def recalculate_meet_statistics(meet_id: int, db: Session = Depends(get_db)):
  """
  Recalcula las estadísticas de asistencia de una reunión
  """
  meet = crud.update_meet_statistics(db, meet_id)
  if not meet:
    raise HTTPException(status_code=404, detail="Meet not found")

  return {
    "message": "Statistics updated successfully",
    "total_neighbors": meet.total_neighbors,
    "total_present": meet.total_present,
    "total_absent": meet.total_absent,
    "total_on_time": meet.total_on_time
  }


@app.post("/meets/recalculate-all-statistics")
def recalculate_all_meets_statistics(db: Session = Depends(get_db)):
  """
  Recalcula las estadísticas de asistencia de todas las reuniones
  """
  meets = crud.get_meets(db)
  updated_count = 0

  for meet in meets:
    crud.update_meet_statistics(db, meet.id)
    updated_count += 1

  return {
    "message": f"Statistics updated successfully for {updated_count} meetings",
    "updated_count": updated_count
  }


# ========== ENDPOINTS DE RECAUDACIONES ==========

@app.get("/collect-debts")
def read_collect_debts(db: Session = Depends(get_db)):
  """
  Obtiene todas las recaudaciones ordenadas por fecha de creación descendente
  """
  collect_debts = crud.get_collect_debts(db)

  collect_debts_data = []
  for cd in collect_debts:
    collect_debts_data.append({
      "id": cd.id,
      "collect_date": str(cd.collect_date),
      "period": cd.period,
      "collector_name": cd.collector_name,
      "location": cd.location,
      "status": cd.status,
      "total_payments": cd.total_payments,
      "total_collected": cd.total_collected,
      "total_neighbors_paid": cd.total_neighbors_paid,
      "start_time": str(cd.start_time) if cd.start_time else None,
      "end_time": str(cd.end_time) if cd.end_time else None,
      "notes": cd.notes,
      "created_at": str(cd.created_at),
      "updated_at": str(cd.updated_at)
    })

  return collect_debts_data


@app.post("/collect-debts", response_model=schemas.CollectDebt)
def create_collect_debt(collect_debt: schemas.CollectDebtCreate, db: Session = Depends(get_db)):
  """
  Crea una nueva recaudación
  """
  db_collect_debt = crud.create_collect_debt(db=db, collect_debt=collect_debt)

  return {
    "id": db_collect_debt.id,
    "collect_date": str(db_collect_debt.collect_date),
    "period": db_collect_debt.period,
    "collector_name": db_collect_debt.collector_name,
    "location": db_collect_debt.location,
    "status": db_collect_debt.status,
    "total_payments": db_collect_debt.total_payments,
    "total_collected": db_collect_debt.total_collected,
    "total_neighbors_paid": db_collect_debt.total_neighbors_paid,
    "start_time": str(db_collect_debt.start_time) if db_collect_debt.start_time else None,
    "end_time": str(db_collect_debt.end_time) if db_collect_debt.end_time else None,
    "notes": db_collect_debt.notes,
    "created_at": str(db_collect_debt.created_at),
    "updated_at": str(db_collect_debt.updated_at)
  }


@app.put("/collect-debts/{collect_debt_id}", response_model=schemas.CollectDebt)
def update_collect_debt(collect_debt_id: int, collect_debt: schemas.CollectDebtUpdate, db: Session = Depends(get_db)):
  """
  Actualiza una recaudación existente
  """
  db_collect_debt = crud.update_collect_debt(db, collect_debt_id=collect_debt_id, collect_debt=collect_debt)
  if db_collect_debt is None:
    raise HTTPException(status_code=404, detail="CollectDebt not found")

  return {
    "id": db_collect_debt.id,
    "collect_date": str(db_collect_debt.collect_date),
    "period": db_collect_debt.period,
    "collector_name": db_collect_debt.collector_name,
    "location": db_collect_debt.location,
    "status": db_collect_debt.status,
    "total_payments": db_collect_debt.total_payments,
    "total_collected": db_collect_debt.total_collected,
    "total_neighbors_paid": db_collect_debt.total_neighbors_paid,
    "start_time": str(db_collect_debt.start_time) if db_collect_debt.start_time else None,
    "end_time": str(db_collect_debt.end_time) if db_collect_debt.end_time else None,
    "notes": db_collect_debt.notes,
    "created_at": str(db_collect_debt.created_at),
    "updated_at": str(db_collect_debt.updated_at)
  }


@app.delete("/collect-debts/{collect_debt_id}")
def delete_collect_debt(collect_debt_id: int, db: Session = Depends(get_db)):
  """
  Elimina una recaudación
  """
  success = crud.delete_collect_debt(db, collect_debt_id=collect_debt_id)
  if not success:
    raise HTTPException(status_code=404, detail="CollectDebt not found")
  return {"ok": True}


@app.get("/collect-debts/{collect_debt_id}/payments")
def get_collect_debt_payments(collect_debt_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todos los pagos de una recaudación específica con detalles
  """
  # Verificar que la recaudación existe
  collect_debt = crud.get_collect_debt(db, collect_debt_id=collect_debt_id)
  if collect_debt is None:
    raise HTTPException(status_code=404, detail="CollectDebt not found")

  payments = db.query(model.Payment).filter(
    model.Payment.collect_debt_id == collect_debt_id
  ).order_by(model.Payment.payment_date.desc()).all()

  payments_data = []
  for payment in payments:
    # Obtener información del vecino
    neighbor = payment.neighbor
    neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

    # Obtener detalles del pago
    payment_details_list = []
    for detail in payment.payment_details:
      debt_item = detail.debt_item
      payment_details_list.append({
        "id": detail.id,
        "debt_item_id": detail.debt_item_id,
        "debt_reason": debt_item.reason if debt_item else "Desconocido",
        "debt_type_name": debt_item.debt_type.name if debt_item and debt_item.debt_type else "Desconocido",
        "amount_applied": detail.amount_applied,
        "previous_balance": detail.previous_balance,
        "new_balance": detail.new_balance,
        "notes": detail.notes
      })

    payments_data.append({
      "id": payment.id,
      "neighbor_id": payment.neighbor_id,
      "neighbor_name": neighbor_name,
      "neighbor_ci": neighbor.ci,
      "collect_debt_id": payment.collect_debt_id,
      "payment_date": str(payment.payment_date),
      "total_amount": payment.total_amount,
      "payment_method": payment.payment_method,
      "reference_number": payment.reference_number,
      "received_by": payment.received_by,
      "notes": payment.notes,
      "created_at": str(payment.created_at),
      "payment_details": payment_details_list
    })

  return payments_data


@app.post("/collect-debts/{collect_debt_id}/payments")
def create_collect_debt_payment(
  collect_debt_id: int,
  neighbor_id: int,
  total_amount: float,
  payment_method: str = None,
  reference_number: str = None,
  received_by: str = None,
  notes: str = None,
  debt_items: list[dict] = None,
  db: Session = Depends(get_db)
):
  """
  Crea un nuevo pago en una recaudación
  debt_items debe ser una lista de objetos con: debt_item_id y amount_applied
  """
  from datetime import datetime

  # Verificar que la recaudación existe
  collect_debt = crud.get_collect_debt(db, collect_debt_id=collect_debt_id)
  if collect_debt is None:
    raise HTTPException(status_code=404, detail="CollectDebt not found")

  # Verificar que el vecino existe
  neighbor = crud.get_neighbor(db, neighbor_id=neighbor_id)
  if neighbor is None:
    raise HTTPException(status_code=404, detail="Neighbor not found")

  # Crear el pago
  db_payment = model.Payment(
    neighbor_id=neighbor_id,
    collect_debt_id=collect_debt_id,
    payment_date=datetime.utcnow().date(),
    total_amount=total_amount,
    payment_method=payment_method,
    reference_number=reference_number,
    received_by=received_by,
    notes=notes
  )
  db.add(db_payment)
  db.flush()  # Para obtener el ID sin hacer commit

  # Crear detalles del pago si se proporcionaron
  if debt_items:
    for item in debt_items:
      debt_item_id = item.get("debt_item_id")
      amount_applied = item.get("amount_applied")

      # Obtener la deuda
      debt_item = crud.get_debt_item(db, debt_id=debt_item_id)
      if debt_item:
        previous_balance = debt_item.balance
        new_balance = previous_balance - amount_applied

        # Crear detalle de pago
        payment_detail = model.PaymentDetail(
          payment_id=db_payment.id,
          debt_item_id=debt_item_id,
          amount_applied=amount_applied,
          previous_balance=previous_balance,
          new_balance=new_balance
        )
        db.add(payment_detail)

        # Actualizar la deuda
        debt_item.amount_paid += amount_applied
        debt_item.balance = new_balance

        # Actualizar estado de la deuda
        if debt_item.balance <= 0:
          debt_item.status = "paid"
          debt_item.paid_date = datetime.utcnow()
        elif debt_item.amount_paid > 0:
          debt_item.status = "partial"

  # Actualizar estadísticas de la recaudación
  collect_debt.total_payments += 1
  collect_debt.total_collected += total_amount

  # Contar vecinos únicos que han pagado
  unique_neighbors = db.query(model.Payment.neighbor_id).filter(
    model.Payment.collect_debt_id == collect_debt_id
  ).distinct().count()
  collect_debt.total_neighbors_paid = unique_neighbors

  db.commit()
  db.refresh(db_payment)

  # Obtener nombre del vecino para la respuesta
  neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

  return {
    "id": db_payment.id,
    "neighbor_id": db_payment.neighbor_id,
    "neighbor_name": neighbor_name,
    "collect_debt_id": db_payment.collect_debt_id,
    "payment_date": str(db_payment.payment_date),
    "total_amount": db_payment.total_amount,
    "payment_method": db_payment.payment_method,
    "reference_number": db_payment.reference_number,
    "received_by": db_payment.received_by,
    "notes": db_payment.notes,
    "created_at": str(db_payment.created_at)
  }