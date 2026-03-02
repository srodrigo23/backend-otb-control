from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class Measure(Base):
  """Mediciones/Jornadas de lectura de medidores"""
  __tablename__ = "measures"

  id = Column(Integer, primary_key=True, index=True)

  measure_date = Column(Date, nullable=False, index=True)  # Fecha de la medición
  period = Column(String(20))  # Periodo (ej: "2025-01", "Enero 2025")

  reader_name = Column(String(100))  # Nombre de la persona que realizó la lectura
  status = Column(String(20), default="in_progress")  # in_progress, completed, cancelled

  total_meters = Column(Integer, default=0)  # Total de medidores a leer
  meters_read = Column(Integer, default=0)  # Medidores ya leídos
  meters_pending = Column(Integer, default=0)  # Medidores pendientes

  notes = Column(String(200))  # Observaciones generales de la jornada
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  meter_readings = relationship("MeterReading", back_populates="measure", cascade="all, delete-orphan")
