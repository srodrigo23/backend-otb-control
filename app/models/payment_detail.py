from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class PaymentDetail(Base):
  """Detalle de pagos - relación muchos a muchos entre Payment y DebtItem"""
  __tablename__ = "payment_details"

  id = Column(Integer, primary_key=True, index=True)
  payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
  debt_item_id = Column(Integer, ForeignKey("debt_items.id"), nullable=False)

  amount_applied = Column(Integer, nullable=False)  # Monto aplicado a esta deuda específica

  previous_balance = Column(Integer)  # Saldo previo de la deuda antes de este pago
  new_balance = Column(Integer)  # Nuevo saldo después de este pago

  notes = Column(String(200))  # Observaciones específicas de este detalle

  created_at = Column(DateTime, default=datetime.utcnow)

  # Relaciones
  payment = relationship("Payment", back_populates="payment_details")
  debt_item = relationship("DebtItem", back_populates="payment_details")
