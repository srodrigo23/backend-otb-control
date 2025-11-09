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