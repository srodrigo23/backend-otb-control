from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class Meet(Base):
  """Reuniones del barrio"""
  __tablename__ = "meets"

  id = Column(Integer, primary_key=True, index=True)

  meet_date = Column(DateTime, nullable=False, index=True)  # Fecha y hora de la reunión
  meet_type = Column(String(50), nullable=False)  # Tipo: "ordinaria", "extraordinaria", "emergencia", "directiva"

  title = Column(String(150), nullable=False)  # Título/Asunto de la reunión
  description = Column(String(500))  # Descripción o agenda de la reunión
  location = Column(String(200))  # Lugar de la reunión

  start_time = Column(DateTime)  # Hora de inicio real
  end_time = Column(DateTime)  # Hora de finalización

  status = Column(String(20), default="scheduled")  # scheduled, in_progress, completed, cancelled
  is_mandatory = Column(Boolean, default=False)  # Si la asistencia es obligatoria

  total_neighbors = Column(Integer, default=0)  # Total de vecinos esperados
  total_present = Column(Integer, default=0)  # Total de asistentes
  total_absent = Column(Integer, default=0)  # Total de ausentes
  total_on_time = Column(Integer, default=0)  # Total que llegaron a tiempo

  organizer = Column(String(100))  # Persona que organiza/convoca
  notes = Column(String(500))  # Notas generales de la reunión

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  assistances = relationship("Assistance", back_populates="meet", cascade="all, delete-orphan")
