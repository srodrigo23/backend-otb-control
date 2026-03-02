from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class Payment(Base):
  """Pagos realizados por los vecinos"""
  __tablename__ = "payments"

  id = Column(Integer, primary_key=True, index=True)
  neighbor_id = Column(Integer, ForeignKey("neighbors.id"), nullable=False)
  collect_debt_id = Column(Integer, ForeignKey("collect_debts.id"))  # FK a la jornada de cobro

  payment_date = Column(Date, nullable=False, default=datetime.utcnow)
  total_amount = Column(Integer, nullable=False)  # Monto total del pago en centavos
  payment_method = Column(String(20))  # cash, transfer, qr, card

  reference_number = Column(String(50))  # Número de referencia/recibo/transacción
  received_by = Column(String(100))  # Persona que recibió el pago

  notes = Column(String(200))

  created_at = Column(DateTime, default=datetime.utcnow)

  # Relaciones
  neighbor = relationship("Neighbor")
  collect_debt = relationship("CollectDebt", back_populates="payments")
  payment_details = relationship("PaymentDetail", back_populates="payment", cascade="all, delete-orphan")
