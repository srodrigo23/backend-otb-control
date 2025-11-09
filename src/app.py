from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
# config for CORS
origins = [
    "http://localhost:5173",
    #"http://localhost:8000",
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
    "debts": debt_details
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
    "debts": debt_details
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