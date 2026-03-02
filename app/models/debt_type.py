from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

class DebtType(Base):
  """Tipos de deuda"""
  __tablename__ = "debt_types"

  id = Column(Integer, primary_key=True, index=True)

  name = Column(String(50), nullable=False, unique=True)  # Ej: "Consumo de Agua", "Multa por Inasistencia"
  description = Column(String(200))  # Descripción del tipo de deuda
  # default_amount = Column(Integer)  # Monto por defecto en centavos

  # is_active = Column(Boolean, default=True)

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  debt_items = relationship("DebtItem", back_populates="debt_type")