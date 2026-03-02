from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Assistance(Base):
  """Registro de asistencia de vecinos a reuniones"""
  __tablename__ = "assistances"

  id = Column(Integer, primary_key=True, index=True)
  meet_id = Column(Integer, ForeignKey("meets.id"), nullable=False)
  neighbor_id = Column(Integer, ForeignKey("neighbors.id"), nullable=False)

  is_present = Column(Boolean, default=False)  # Si asistió
  is_on_time = Column(Boolean, default=False)  # Si llegó a tiempo

  arrival_time = Column(DateTime)  # Hora exacta de llegada
  departure_time = Column(DateTime)  # Hora de salida (opcional)

  excuse_reason = Column(String(200))  # Razón de ausencia (si aplica)
  has_excuse = Column(Boolean, default=False)  # Si presentó justificación

  represented_by = Column(String(100))  # Nombre de quien lo representó (si aplica)
  has_representative = Column(Boolean, default=False)  # Si envió representante

  notes = Column(String(200))  # Observaciones específicas

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  meet = relationship("Meet", back_populates="assistances")
  neighbor = relationship("Neighbor", back_populates="assistances")
  debt_item = relationship("DebtItem", back_populates="assistance", uselist=False)