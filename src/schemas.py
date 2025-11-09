from pydantic import BaseModel


class ItemBase(BaseModel):
  title: str
  # description: str | None = None


class ItemCreate(ItemBase):
  pass


class Item(ItemBase):
  id: int
  owner_id: int

  class Config:
    from_attributes = True


class NeighborBase(BaseModel):
  email: str | None = None


class NeighborCreate(BaseModel):
  first_name: str
  second_name: str | None = None
  last_name: str
  ci: str
  phone_number: str | int
  email: str | None = None


class NeighborUpdate(BaseModel):
  first_name: str | None = None
  second_name: str | None = None
  last_name: str | None = None
  ci: str | None = None
  phone_number: int | None = None
  email: str | None = None


class Neighbor(BaseModel):
  id: int
  first_name: str
  second_name: str | None = None
  email: str | None = None
  last_name: str
  ci: int
  phone_number: int

  class Config:
    from_attributes = True


# Schemas para DebtType
class DebtTypeBase(BaseModel):
  name: str
  description: str | None = None


class DebtType(DebtTypeBase):
  id: int
  created_at: str
  updated_at: str

  class Config:
    from_attributes = True


# Schemas para DebtItem
class DebtItemBase(BaseModel):
  neighbor_id: int
  debt_type_id: int
  amount: int
  reason: str
  period: str | None = None


class DebtItemDetail(BaseModel):
  id: int
  neighbor_id: int
  debt_type_id: int
  debt_type_name: str  # Nombre del tipo de deuda
  meter_reading_id: int | None = None
  assistance_id: int | None = None
  amount: int  # Monto total en centavos
  amount_paid: int  # Monto ya pagado
  balance: int  # Saldo pendiente
  reason: str
  period: str | None = None
  issue_date: str
  due_date: str | None = None
  paid_date: str | None = None
  status: str
  is_overdue: bool
  late_fee: int
  discount: int
  notes: str | None = None

  class Config:
    from_attributes = True


# Schema para respuesta de deudas de un vecino
class NeighborDebtsResponse(BaseModel):
  neighbor_id: int
  neighbor_name: str
  total_debts: int  # Total de deudas activas
  total_amount: int  # Monto total adeudado en centavos
  total_balance: int  # Saldo total pendiente
  debts: list[DebtItemDetail]


# Schemas para Measure (Mediciones)
class MeasureBase(BaseModel):
  measure_date: str  # Fecha en formato string
  period: str | None = None
  reader_name: str | None = None
  notes: str | None = None


class MeasureCreate(MeasureBase):
  pass


class MeasureUpdate(BaseModel):
  measure_date: str | None = None
  period: str | None = None
  reader_name: str | None = None
  status: str | None = None
  total_meters: int | None = None
  meters_read: int | None = None
  meters_pending: int | None = None
  notes: str | None = None


class Measure(BaseModel):
  id: int
  measure_date: str
  period: str | None = None
  reader_name: str | None = None
  status: str
  total_meters: int
  meters_read: int
  meters_pending: int
  notes: str | None = None
  created_at: str
  updated_at: str

  class Config:
    from_attributes = True 