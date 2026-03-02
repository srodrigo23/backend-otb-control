from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class NeighborMeter(Base):
  """Medidores asociados a cada vecino"""
  __tablename__ = "neighbor_meters"

  id = Column(Integer, primary_key=True, index=True)
  neighbor_id = Column(Integer, ForeignKey("neighbors.id"), nullable=False)

  meter_code = Column(String(50), unique=True, nullable=False, index=True)  # Código único del medidor
  label = Column(String(100))  # Etiqueta descriptiva (ej: "Medidor Principal", "Medidor Jardín")

  is_active = Column(Boolean, default=True)  # Si el medidor está activo
  installation_date = Column(Date)  # Fecha de instalación del medidor
  last_maintenance_date = Column(Date)  # Última fecha de mantenimiento

  notes = Column(String(200))  # Notas adicionales sobre el medidor
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  neighbor = relationship("Neighbor", back_populates="meters")
  readings = relationship("MeterReading", back_populates="meter", cascade="all, delete-orphan")