from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class CollectDebt(Base):
  """Jornadas de cobro de deudas"""
  __tablename__ = "collect_debts"

  id = Column(Integer, primary_key=True, index=True)

  collect_date = Column(Date, nullable=False, index=True)  # Fecha de la jornada de cobro
  period = Column(String(20))  # Periodo (ej: "2025-01", "Enero 2025")

  collector_name = Column(String(100))  # Nombre del cobrador/responsable
  location = Column(String(200))  # Lugar donde se realiza el cobro

  status = Column(String(20), default="in_progress")  # in_progress, completed, cancelled

  # Estadísticas
  total_payments = Column(Integer, default=0)  # Total de pagos recibidos
  total_collected = Column(Integer, default=0)  # Monto total cobrado en centavos
  total_neighbors_paid = Column(Integer, default=0)  # Total de vecinos que pagaron

  start_time = Column(DateTime)  # Hora de inicio de la jornada
  end_time = Column(DateTime)  # Hora de finalización

  notes = Column(String(500))  # Observaciones generales de la jornada

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  payments = relationship("Payment", back_populates="collect_debt", cascade="all, delete-orphan")
