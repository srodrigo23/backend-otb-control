from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from .. import models
from ..schemas import schema as schemas
from ..services import crud
from ..dependencies import get_db

router = APIRouter(
  prefix="/debts", 
  tags=['Dets'], 
  responses={404: {"description": "Not found"}}
)

@router.post("/migrate-to-bolivianos")
def migrate_debtsto_bolivianos(db: Session = Depends(get_db)):
  """
  Convierte todas las deudas y pagos de centavos a bolivianos (divide por 100)
  IMPORTANTE: Ejecutar solo una vez para migrar datos existentes
  """
  # Migrar DebtItems
  debts = db.query(models.DebtItem).all()
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
  payments = db.query(models.Payment).all()
  payments_updated = 0

  for payment in payments:
    payment.total_amount = payment.total_amount / 100
    payments_updated += 1

  # Migrar PaymentDetails
  payment_details = db.query(models.PaymentDetail).all()
  details_updated = 0

  for detail in payment_details:
    detail.amount_applied = detail.amount_applied / 100
    if detail.previous_balance:
      detail.previous_balance = detail.previous_balance / 100
    if detail.new_balance:
      detail.new_balance = detail.new_balance / 100
    details_updated += 1

  # Migrar CollectDebts
  collect_debts = db.query(models.CollectDebt).all()
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


@router.get("/{debt_id}")
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
