from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Neighbor(Base):
  """Vecinos registrados en el sistema"""
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


class MeterReading(Base):
  """Lecturas individuales de medidores en una medición"""
  __tablename__ = "meter_readings"

  id = Column(Integer, primary_key=True, index=True)
  measure_id = Column(Integer, ForeignKey("measures.id"), nullable=False)
  meter_id = Column(Integer, ForeignKey("neighbor_meters.id"), nullable=False)

  current_reading = Column(Integer, nullable=False)  # Lectura actual del medidor
  # previous_reading = Column(Integer, default=0)  # Lectura anterior
  # consumption = Column(Integer)  # Consumo calculado (current_reading - previous_reading)

  reading_date = Column(DateTime, default=datetime.utcnow)  # Fecha y hora exacta de la lectura
  # reader_name = Column(String(100))  # Persona que realizó esta lectura específica

  status = Column(String(20), default="normal")  # normal, estimated, not_read, meter_error
  has_anomaly = Column(Boolean, default=False)  # Si hay alguna anomalía detectada

  notes = Column(String(200))  # Observaciones específicas de esta lectura
  # photo_url = Column(String(200))  # URL de la foto del medidor (opcional)

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  measure = relationship("Measure", back_populates="meter_readings")
  meter = relationship("NeighborMeter", back_populates="readings")
  debt_item = relationship("DebtItem", back_populates="meter_reading", uselist=False)


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


class Assistance(Base):
  """Registro de asistencia de vecinos a reuniones"""
  __tablename__ = "assistances"

  id = Column(Integer, primary_key=True, index=True)
  meet_id = Column(Integer, ForeignKey("meets.id"), nullable=False)
  neighbor_id = Column(Integer, ForeignKey("neighbors.id"), nullable=False)

  is_present = Column(Boolean, default=False)  # Si asistió
  is_on_time = Column(Boolean, default=False)  # Si llegó a tiempo

  arrival_time = Column(DateTime)  # Hora exacta de llegada
  departure_time = Column(DateTime)  # Hora de salida (opcional)

  excuse_reason = Column(String(200))  # Razón de ausencia (si aplica)
  has_excuse = Column(Boolean, default=False)  # Si presentó justificación

  represented_by = Column(String(100))  # Nombre de quien lo representó (si aplica)
  has_representative = Column(Boolean, default=False)  # Si envió representante

  notes = Column(String(200))  # Observaciones específicas

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  meet = relationship("Meet", back_populates="assistances")
  neighbor = relationship("Neighbor", back_populates="assistances")
  debt_item = relationship("DebtItem", back_populates="assistance", uselist=False)


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


class DebtItem(Base):
  """Registro de deudas de los vecinos"""
  __tablename__ = "debt_items"

  id = Column(Integer, primary_key=True, index=True)
  neighbor_id = Column(Integer, ForeignKey("neighbors.id"), nullable=False)
  debt_type_id = Column(Integer, ForeignKey("debt_types.id"), nullable=False)

  # Referencias opcionales según el origen de la deuda
  meter_reading_id = Column(Integer, ForeignKey("meter_readings.id"))  # Si es por consumo de agua
  assistance_id = Column(Integer, ForeignKey("assistances.id"))  # Si es por inasistencia a reunión

  amount = Column(Integer, nullable=False)  # Monto de la deuda en centavos
  amount_paid = Column(Integer, default=0)  # Monto ya pagado
  balance = Column(Integer, nullable=False)  # Saldo pendiente

  reason = Column(String(200), nullable=False)  # Motivo/descripción de la deuda
  period = Column(String(20))  # Periodo (ej: "2025-01", "Enero 2025")

  # Fechas
  issue_date = Column(Date, nullable=False, default=datetime.utcnow)  # Fecha de emisión
  due_date = Column(Date)  # Fecha límite de pago
  paid_date = Column(Date)  # Fecha en que se pagó completamente

  # Estado
  status = Column(String(20), default="pending")  # pending, partial, paid, overdue, cancelled
  is_overdue = Column(Boolean, default=False)  # Si está vencida

  # Información adicional
  late_fee = Column(Integer, default=0)  # Recargo por mora
  discount = Column(Integer, default=0)  # Descuento aplicado

  notes = Column(String(200))  # Notas adicionales

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  neighbor = relationship("Neighbor", back_populates="debts")
  debt_type = relationship("DebtType", back_populates="debt_items")
  meter_reading = relationship("MeterReading", back_populates="debt_item")
  assistance = relationship("Assistance", back_populates="debt_item")
  payment_details = relationship("PaymentDetail", back_populates="debt_item", cascade="all, delete-orphan")


class CollectDebt(Base):
  """Jornadas de cobro de deudas"""
  __tablename__ = "collect_debts"

  id = Column(Integer, primary_key=True, index=True)

  collect_date = Column(Date, nullable=False, index=True)  # Fecha de la jornada de cobro
  period = Column(String(20))  # Periodo (ej: "2025-01", "Enero 2025")

  collector_name = Column(String(100))  # Nombre del cobrador/responsable
  location = Column(String(200))  # Lugar donde se realiza el cobro

  status = Column(String(20), default="in_progress")  # in_progress, completed, cancelled

  # Estadísticas
  total_payments = Column(Integer, default=0)  # Total de pagos recibidos
  total_collected = Column(Integer, default=0)  # Monto total cobrado en centavos
  total_neighbors_paid = Column(Integer, default=0)  # Total de vecinos que pagaron

  start_time = Column(DateTime)  # Hora de inicio de la jornada
  end_time = Column(DateTime)  # Hora de finalización

  notes = Column(String(500))  # Observaciones generales de la jornada

  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  # Relaciones
  payments = relationship("Payment", back_populates="collect_debt", cascade="all, delete-orphan")


class Payment(Base):
  """Pagos realizados por los vecinos"""
  __tablename__ = "payments"

  id = Column(Integer, primary_key=True, index=True)
  neighbor_id = Column(Integer, ForeignKey("neighbors.id"), nullable=False)
  collect_debt_id = Column(Integer, ForeignKey("collect_debts.id"))  # FK a la jornada de cobro

  payment_date = Column(Date, nullable=False, default=datetime.utcnow)
  total_amount = Column(Integer, nullable=False)  # Monto total del pago en centavos
  payment_method = Column(String(20))  # cash, transfer, qr, card

  reference_number = Column(String(50))  # Número de referencia/recibo/transacción
  received_by = Column(String(100))  # Persona que recibió el pago

  notes = Column(String(200))

  created_at = Column(DateTime, default=datetime.utcnow)

  # Relaciones
  neighbor = relationship("Neighbor")
  collect_debt = relationship("CollectDebt", back_populates="payments")
  payment_details = relationship("PaymentDetail", back_populates="payment", cascade="all, delete-orphan")


class PaymentDetail(Base):
  """Detalle de pagos - relación muchos a muchos entre Payment y DebtItem"""
  __tablename__ = "payment_details"

  id = Column(Integer, primary_key=True, index=True)
  payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
  debt_item_id = Column(Integer, ForeignKey("debt_items.id"), nullable=False)

  amount_applied = Column(Integer, nullable=False)  # Monto aplicado a esta deuda específica

  previous_balance = Column(Integer)  # Saldo previo de la deuda antes de este pago
  new_balance = Column(Integer)  # Nuevo saldo después de este pago

  notes = Column(String(200))  # Observaciones específicas de este detalle

  created_at = Column(DateTime, default=datetime.utcnow)

  # Relaciones
  payment = relationship("Payment", back_populates="payment_details")
  debt_item = relationship("DebtItem", back_populates="payment_details")


# class Item(Base):
#   __tablename__ = "items"

#   id = Column(Integer, primary_key=True)
#   title = Column(String, index=True)
#   description = Column(String, index=True)
#   owner_id = Column(Integer, ForeignKey("users.id"))
#   owner = relationship("User", back_populates="items")