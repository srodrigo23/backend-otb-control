# ========== MEDICIONES ==========
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from .. import models
from ..schemas import schema as schemas
from ..services import crud
from ..dependencies import get_db

router = APIRouter(
  prefix="/measures", 
  tags=['Measures'], 
  responses={404: {"description": "Not found"}}
)

@router.get("")
def read_measures(db: Session = Depends(get_db)):
  """
  Obtiene todas las mediciones ordenadas por fecha de creación
  """
  measures = crud.get_measures(db)

  # Convertir las fechas a string para la respuesta
  measures_data = []
  for measure in measures:
    measures_data.append({
      "id": measure.id,
      "measure_date": str(measure.measure_date),
      "period": measure.period,
      "reader_name": measure.reader_name,
      "status": measure.status,
      "total_meters": measure.total_meters,
      "meters_read": measure.meters_read,
      "meters_pending": measure.meters_pending,
      "notes": measure.notes,
      "created_at": str(measure.created_at),
      "updated_at": str(measure.updated_at)
    })

  return measures_data


@router.get("/{measure_id}", response_model=schemas.Measure)
def read_measure(measure_id: int, db: Session = Depends(get_db)):
  """
  Obtiene una medición específica
  """
  measure = crud.get_measure(db, measure_id=measure_id)
  if measure is None:
    raise HTTPException(status_code=404, detail="Measure not found")

  return {
    "id": measure.id,
    "measure_date": str(measure.measure_date),
    "period": measure.period,
    "reader_name": measure.reader_name,
    "status": measure.status,
    "total_meters": measure.total_meters,
    "meters_read": measure.meters_read,
    "meters_pending": measure.meters_pending,
    "notes": measure.notes,
    "created_at": str(measure.created_at),
    "updated_at": str(measure.updated_at)
  }


@router.post("", response_model=schemas.Measure)
def create_measure(measure: schemas.MeasureCreate, db: Session = Depends(get_db)):
  """
  Crea una nueva medición
  """
  db_measure = crud.create_measure(db=db, measure=measure)

  return {
    "id": db_measure.id,
    "measure_date": str(db_measure.measure_date),
    "period": db_measure.period,
    "reader_name": db_measure.reader_name,
    "status": db_measure.status,
    "total_meters": db_measure.total_meters,
    "meters_read": db_measure.meters_read,
    "meters_pending": db_measure.meters_pending,
    "notes": db_measure.notes,
    "created_at": str(db_measure.created_at),
    "updated_at": str(db_measure.updated_at)
  }


@router.put("/{measure_id}", response_model=schemas.Measure)
def update_measure(measure_id: int, measure: schemas.MeasureUpdate, db: Session = Depends(get_db)):
  """
  Actualiza una medición existente
  """
  db_measure = crud.update_measure(db, measure_id=measure_id, measure=measure)
  if db_measure is None:
    raise HTTPException(status_code=404, detail="Measure not found")

  return {
    "id": db_measure.id,
    "measure_date": str(db_measure.measure_date),
    "period": db_measure.period,
    "reader_name": db_measure.reader_name,
    "status": db_measure.status,
    "total_meters": db_measure.total_meters,
    "meters_read": db_measure.meters_read,
    "meters_pending": db_measure.meters_pending,
    "notes": db_measure.notes,
    "created_at": str(db_measure.created_at),
    "updated_at": str(db_measure.updated_at)
  }


@router.delete("/{measure_id}")
def delete_measure(measure_id: int, db: Session = Depends(get_db)):
  """
  Elimina una medición
  """
  success = crud.delete_measure(db, measure_id=measure_id)
  if not success:
    raise HTTPException(status_code=404, detail="Measure not found")
  return {"message": "Measure deleted successfully", "id": measure_id}


@router.get("/{measure_id}/meter-readings")
def get_measure_meter_readings(measure_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todas las lecturas de medidores para una medición específica
  """
  # Verificar que la medición existe
  measure = crud.get_measure(db, measure_id=measure_id)
  if not measure:
    raise HTTPException(status_code=404, detail="Measure not found")

  # Obtener todas las lecturas de esta medición con información del vecino y medidor
  meter_readings = db.query(models.MeterReading).filter(
    models.MeterReading.measure_id == measure_id
  ).join(
    models.NeighborMeter, models.MeterReading.meter_id == models.NeighborMeter.id
  ).join(
    models.Neighbor, models.NeighborMeter.neighbor_id == models.Neighbor.id
  ).order_by(models.Neighbor.last_name, models.Neighbor.first_name).all()

  # Formatear respuesta con información del vecino
  readings_data = []
  for reading in meter_readings:
    neighbor = reading.meter.neighbor
    readings_data.append({
      "id": reading.id,
      "meter_id": reading.meter_id,
      "measure_id": reading.measure_id,
      "current_reading": reading.current_reading,
      "reading_date": str(reading.reading_date),
      "status": reading.status,
      "has_anomaly": reading.has_anomaly,
      "notes": reading.notes,
      "created_at": str(reading.created_at),
      "updated_at": str(reading.updated_at),
      # Información del vecino
      "neighbor_first_name": neighbor.first_name,
      "neighbor_second_name": neighbor.second_name,
      "neighbor_last_name": neighbor.last_name,
      "neighbor_ci": neighbor.ci,
      # Información del medidor
      "meter_number": reading.meter.meter_code,
    })

  return readings_data

@router.post("/{measure_id}/generate-debts")
def generate_debts_from_measure(measure_id: int, db: Session = Depends(get_db)):
  """
  Genera deudas de consumo de agua para todos los vecinos basándose en las lecturas de una medición
  Lógica de cobro:
  - Consumo <= 20 m3: Bs. 20
  - Consumo > 20 m3: Bs. 1 por m3
  """
  # Verificar que la medición existe
  measure = crud.get_measure(db, measure_id=measure_id)
  if not measure:
    raise HTTPException(status_code=404, detail="Measure not found")

  # Obtener o crear el tipo de deuda "Consumo de Agua"
  debt_type = db.query(models.DebtType).filter(models.DebtType.name == "Consumo de Agua").first()
  if not debt_type:
    debt_type = models.DebtType(
      name="Consumo de Agua",
      description="Deuda por consumo de agua mensual"
    )
    db.add(debt_type)
    db.commit()
    db.refresh(debt_type)

  # Obtener todas las lecturas de esta medición
  meter_readings = db.query(models.MeterReading).filter(
    models.MeterReading.measure_id == measure_id
  ).join(
    models.NeighborMeter, models.MeterReading.meter_id == models.NeighborMeter.id
  ).all()

  debts_created = 0
  debts_skipped = 0
  debts_details = []

  for reading in meter_readings:
    # Verificar si ya existe una deuda para esta lectura
    existing_debt = db.query(models.DebtItem).filter(
      models.DebtItem.meter_reading_id == reading.id
    ).first()

    if existing_debt:
      debts_skipped += 1
      continue

    # Obtener la lectura anterior del mismo medidor
    previous_reading = db.query(models.MeterReading).filter(
      models.MeterReading.meter_id == reading.meter_id,
      models.MeterReading.id < reading.id
    ).order_by(models.MeterReading.id.desc()).first()

    # Calcular consumo
    if previous_reading:
      consumption = reading.current_reading - previous_reading.current_reading
    else:
      # Si no hay lectura anterior, usar la lectura actual como consumo
      consumption = reading.current_reading

    # Calcular monto según la lógica (en bolivianos)
    if consumption <= 20:
      amount = 20  # Bs. 20
    else:
      amount = consumption  # Bs. 1 por m3

    # Crear la deuda
    from datetime import date
    debt_item = models.DebtItem(
      neighbor_id=reading.meter.neighbor_id,
      debt_type_id=debt_type.id,
      meter_reading_id=reading.id,
      amount=amount,
      amount_paid=0,
      balance=amount,
      reason=f"Consumo de agua - {consumption} m3",
      period=measure.period,
      issue_date=date.today(),
      status="pending"
    )
    db.add(debt_item)
    debts_created += 1

    debts_details.append({
      "neighbor_id": reading.meter.neighbor_id,
      "neighbor_name": f"{reading.meter.neighbor.first_name} {reading.meter.neighbor.last_name}",
      "consumption": consumption,
      "amount": amount,
      "meter_reading_id": reading.id
    })

  db.commit()

  return {
    "message": f"Debts generated successfully",
    "debts_created": debts_created,
    "debts_skipped": debts_skipped,
    "total_readings": len(meter_readings),
    "details": debts_details
  }


@router.delete("/{measure_id}/debts")
def delete_measure_debts(measure_id: int, db: Session = Depends(get_db)):
  """
  Elimina todas las deudas generadas para una medición específica
  Solo elimina deudas que no hayan sido pagadas (status = pending)
  """
  # Verificar que la medición existe
  measure = crud.get_measure(db, measure_id=measure_id)
  if not measure:
    raise HTTPException(status_code=404, detail="Measure not found")

  # Obtener todas las lecturas de esta medición
  meter_readings = db.query(models.MeterReading).filter(
    models.MeterReading.measure_id == measure_id
  ).all()

  reading_ids = [reading.id for reading in meter_readings]

  # Eliminar solo las deudas pendientes (no pagadas) asociadas a estas lecturas
  debts_deleted = db.query(models.DebtItem).filter(
    models.DebtItem.meter_reading_id.in_(reading_ids),
    models.DebtItem.status == "pending"
  ).delete(synchronize_session=False)

  db.commit()

  return {
    "message": f"Debts deleted successfully",
    "debts_deleted": debts_deleted
  }
