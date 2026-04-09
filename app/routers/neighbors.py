from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from ..schemas import schema as schemas
from ..services import crud
from ..dependencies import get_db

router = APIRouter(
  prefix="/neighbors", 
  tags=['Neighbors'], 
  responses={404: {"description": "Not found"}}
)

@router.post("", response_model=schemas.Neighbor, )
def create_neighbor(neighbor: schemas.NeighborCreate, db: Session = Depends(get_db)):
  # Validar email solo si se proporciona
  if neighbor.email:
    db_neighbor = crud.get_neighbor_by_email(db, email=neighbor.email)
    if db_neighbor:
      raise HTTPException(status_code=400, detail="Email already registered")
  return crud.create_neighbor(db=db, neighbor=neighbor)

@router.get("")
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

@router.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
  db_user = crud.get_user(db, user_id=user_id)
  if db_user is None:
    raise HTTPException(status_code=404, detail="User not found")
  return db_user


@router.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@router.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@router.put("/{neighbor_id}", response_model=schemas.Neighbor)
def update_neighbor(neighbor_id: int, neighbor: schemas.NeighborUpdate, db: Session = Depends(get_db)):
  db_neighbor = crud.update_neighbor(db, neighbor_id=neighbor_id, neighbor=neighbor)
  if db_neighbor is None:
    raise HTTPException(status_code=404, detail="Neighbor not found")
  return db_neighbor


@router.delete("/{neighbor_id}")
def delete_neighbor(neighbor_id: int, db: Session = Depends(get_db)):
  success = crud.delete_neighbor(db, neighbor_id=neighbor_id)
  if not success:
    raise HTTPException(status_code=404, detail="Neighbor not found")
  return {"message": "Neighbor deleted successfully", "id": neighbor_id}


@router.get("/{neighbor_id}/meters")
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


@router.get("/{neighbor_id}/payments")
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

@router.get("/{neighbor_id}/debts/active", response_model=schemas.NeighborDebtsResponse)
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


@router.get("/{neighbor_id}/debts/all")
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
