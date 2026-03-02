from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class DebtItem(Base):
  """Registro de deudas de los vecinos"""
  __tablename__ = "debt_items"

  id = Column(Integer, primary_key=True, index=True)
  neighbor_id = Column(Integer, ForeignKey("neighbors.id"), nullable=False)
  debt_type_id = Column(Integer, ForeignKey("debt_types.id"), nullable=False)

  # Referencias opcionales según el origen de la deuda
  meter_reading_id = Column(Integer, ForeignKey("meter_readings.id"))  # Si es por consumo de agua
  assistance_id = Column(Integer, ForeignKey("assistances.id"))  # Si es por inasistencia a reunión

  amount = Column(Integer, nullable=False)  # Monto de la deuda en centavos
  amount_paid = Column(Integer, default=0)  # Monto ya pagado
  balance = Column(Integer, nullable=False)  # Saldo pendiente

  reason = Column(String(200), nullable=False)  # Motivo/descripción de la deuda
  period = Column(String(20))  # Periodo (ej: "2025-01", "Enero 2025")

  # Fechas
  issue_date = Column(Date, nullable=False, default=datetime.utcnow)  # Fecha de emisión
  due_date = Column(Date)  # Fecha límite de pago
  paid_date = Column(Date)  # Fecha en que se pagó completamente

  # Estado
  status = Column(String(20), default="pending")  # pending, partial, paid, overdue, cancelled
  is_overdue = Column(Boolean, default=False)  # Si está vencida

  # Información adicional
  late_fee = Column(Integer, default=0)  # Recargo por mora
  discount = Column(Integer, default=0)  # Descuento aplicado

  notes = Column(String(200))  # Notas adicionales

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  neighbor = relationship("Neighbor", back_populates="debts")
  debt_type = relationship("DebtType", back_populates="debt_items")
  meter_reading = relationship("MeterReading", back_populates="debt_item")
  assistance = relationship("Assistance", back_populates="debt_item")
  payment_details = relationship("PaymentDetail", back_populates="debt_item", cascade="all, delete-orphan")