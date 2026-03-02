
from sqlalchemy import Boolean, Column, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Neighbor(Base):
  __tablename__ = "neighbors"

  id = Column(Integer, primary_key=True, index=True)

  first_name = Column(String(30), unique=False, nullable=False)
  second_name = Column(String(30), default="")
  last_name = Column(String(30))

  ci = Column(Integer)
  phone_number = Column(Integer)
  email = Column(String(50))
  birth_day = Column(Date)
  section = Column(String(50))

  is_active = Column(Boolean, default=True)  # Si el vecino está activo
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
  
  # Relaciones
  meters = relationship("NeighborMeter", back_populates="neighbor", cascade="all, delete-orphan")
  assistances = relationship("Assistance", back_populates="neighbor", cascade="all, delete-orphan")
  debts = relationship("DebtItem", back_populates="neighbor", cascade="all, delete-orphan")
  
