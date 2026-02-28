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
  debt_details: list[DebtItemDetail]


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


# Schemas para MeterReading (Lecturas de medidores)
class MeterReading(BaseModel):
  id: int
  meter_id: int
  measure_id: int
  current_reading: int
  reading_date: str
  status: str
  has_anomaly: bool
  notes: str | None = None
  created_at: str
  updated_at: str

  # Información del vecino y medidor
  neighbor_first_name: str | None = None
  neighbor_second_name: str | None = None
  neighbor_last_name: str | None = None
  neighbor_ci: str | None = None
  meter_number: str | None = None

  class Config:
    from_attributes = True


# Schemas para Meet (Reuniones)
class MeetBase(BaseModel):
  meet_date: str  # DateTime en formato string
  meet_type: str
  title: str
  description: str | None = None
  location: str | None = None
  is_mandatory: bool = False
  organizer: str | None = None
  notes: str | None = None


class MeetCreate(MeetBase):
  pass


class MeetUpdate(BaseModel):
  meet_date: str | None = None
  meet_type: str | None = None
  title: str | None = None
  description: str | None = None
  location: str | None = None
  start_time: str | None = None
  end_time: str | None = None
  status: str | None = None
  is_mandatory: bool | None = None
  organizer: str | None = None
  notes: str | None = None


class Meet(BaseModel):
  id: int
  meet_date: str
  meet_type: str
  title: str
  description: str | None = None
  location: str | None = None
  start_time: str | None = None
  end_time: str | None = None
  status: str
  is_mandatory: bool
  total_neighbors: int
  total_present: int
  total_absent: int
  total_on_time: int
  organizer: str | None = None
  notes: str | None = None
  created_at: str
  updated_at: str

  class Config:
    from_attributes = True


# Schemas para Assistance (Asistencia)
class AssistanceBase(BaseModel):
  neighbor_id: int
  is_present: bool = False
  is_on_time: bool = False


class AssistanceCreate(AssistanceBase):
  meet_id: int


class AssistanceUpdate(BaseModel):
  is_present: bool | None = None
  is_on_time: bool | None = None
  arrival_time: str | None = None
  departure_time: str | None = None
  excuse_reason: str | None = None
  has_excuse: bool | None = None
  represented_by: str | None = None
  has_representative: bool | None = None
  notes: str | None = None


class Assistance(BaseModel):
  id: int
  meet_id: int
  neighbor_id: int
  neighbor_name: str | None = None  # Para incluir el nombre del vecino
  is_present: bool
  is_on_time: bool
  arrival_time: str | None = None
  departure_time: str | None = None
  excuse_reason: str | None = None
  has_excuse: bool
  represented_by: str | None = None
  has_representative: bool
  notes: str | None = None

  class Config:
    from_attributes = True


# Schemas para CollectDebt (Recaudaciones)
class CollectDebtBase(BaseModel):
  collect_date: str  # Fecha en formato string
  period: str | None = None
  collector_name: str | None = None
  location: str | None = None
  notes: str | None = None


class CollectDebtCreate(CollectDebtBase):
  pass


class CollectDebtUpdate(BaseModel):
  collect_date: str | None = None
  period: str | None = None
  collector_name: str | None = None
  location: str | None = None
  status: str | None = None
  total_payments: int | None = None
  total_collected: int | None = None
  total_neighbors_paid: int | None = None
  start_time: str | None = None
  end_time: str | None = None
  notes: str | None = None


class CollectDebt(BaseModel):
  id: int
  collect_date: str
  period: str | None = None
  collector_name: str | None = None
  location: str | None = None
  status: str
  total_payments: int
  total_collected: int
  total_neighbors_paid: int
  start_time: str | None = None
  end_time: str | None = None
  notes: str | None = None
  created_at: str
  updated_at: str

  class Config:
    from_attributes = True 