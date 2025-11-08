from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Neighbor(Base):
  __tablename__ = "users"  # Mantener nombre de tabla para compatibilidad

  id = Column(Integer, primary_key=True)

  first_name = Column(String(30), unique=False, nullable=False)
  second_name = Column(String(30), default="")
  last_name = Column(String(30))

  ci = Column(String(10))
  phone_number = Column(String(15))
  email = Column(String(30))

  # items = relationship("Item", back_populates="owner")


# class Item(Base):
#   __tablename__ = "items"

#   id = Column(Integer, primary_key=True)
#   title = Column(String, index=True)
#   description = Column(String, index=True)
#   owner_id = Column(Integer, ForeignKey("users.id"))
#   owner = relationship("User", back_populates="items")