from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from sqlalchemy.orm import relationship

from database import Base


class Neighbor(Base):
  __tablename__ = "neighbors"  # Mantener nombre de tabla para compatibilidad

  id = Column(Integer, primary_key=True)

  first_name = Column(String(30), unique=False, nullable=False)
  second_name = Column(String(30), default="")
  last_name = Column(String(30))

  ci = Column(Integer)
  phone_number = Column(Integer)

  email = Column(String(30))
  birth_day = Column(Date)
  meter_code = Column(String(50))
  section = Column(String(50))
  # items = relationship("Item", back_populates="owner")


# class Item(Base):
#   __tablename__ = "items"

#   id = Column(Integer, primary_key=True)
#   title = Column(String, index=True)
#   description = Column(String, index=True)
#   owner_id = Column(Integer, ForeignKey("users.id"))
#   owner = relationship("User", back_populates="items")