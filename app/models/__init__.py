# class Item(Base):
#   __tablename__ = "items"
#   id = Column(Integer, primary_key=True)
#   title = Column(String, index=True)
#   description = Column(String, index=True)
#   owner_id = Column(Integer, ForeignKey("users.id"))
#   owner = relationship("User", back_populates="items")


from .assistance import Assistance
from .collect_debt import CollectDebt
from .debt_item import DebtItem
from .debt_type import DebtType
from .measure import Measure
from .meet import Meet
from .meter_reading import MeterReading
from .neighbor_meter import NeighborMeter
from .neighbor import Neighbor
from .payment_detail import PaymentDetail
from .payment import Payment

from .user import User