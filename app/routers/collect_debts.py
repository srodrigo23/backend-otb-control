# ========== ENDPOINTS DE RECAUDACIONES ==========
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from .. import models
from ..schemas import schema as schemas
from ..services import crud
from ..dependencies import get_db

router = APIRouter(
  prefix="/collect-debts", 
  tags=['Collect Debts'], 
  responses={404: {"description": "Not found"}}
)

@router.get("")
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


@router.post("", response_model=schemas.CollectDebt)
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


@router.put("/{collect_debt_id}", response_model=schemas.CollectDebt)
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


@router.delete("/{collect_debt_id}")
def delete_collect_debt(collect_debt_id: int, db: Session = Depends(get_db)):
  """
  Elimina una recaudación
  """
  success = crud.delete_collect_debt(db, collect_debt_id=collect_debt_id)
  if not success:
    raise HTTPException(status_code=404, detail="CollectDebt not found")
  return {"ok": True}


@router.get("/{collect_debt_id}/payments")
def get_collect_debt_payments(collect_debt_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todos los pagos de una recaudación específica con detalles
  """
  # Verificar que la recaudación existe
  collect_debt = crud.get_collect_debt(db, collect_debt_id=collect_debt_id)
  if collect_debt is None:
    raise HTTPException(status_code=404, detail="CollectDebt not found")

  payments = db.query(models.Payment).filter(
    models.Payment.collect_debt_id == collect_debt_id
  ).order_by(models.Payment.payment_date.desc()).all()

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


@router.post("/{collect_debt_id}/payments")
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
  db_payment = models.Payment(
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
        payment_detail = models.PaymentDetail(
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
  unique_neighbors = db.query(models.Payment.neighbor_id).filter(
    models.Payment.collect_debt_id == collect_debt_id
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