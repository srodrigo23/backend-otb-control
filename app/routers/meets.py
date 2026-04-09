# ==========  REUNIONES ==========

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from ..schemas import schema as schemas
from ..services import crud
from ..dependencies import get_db

router = APIRouter(
  prefix="/meets", 
  tags=['Meets'], 
  responses={404: {"description": "Not found"}}
)

@router.get("")
def read_meets(db: Session = Depends(get_db)):
  """
  Obtiene todas las reuniones ordenadas por fecha de creación
  """
  meets = crud.get_meets(db)

  # Convertir las fechas a string para la respuesta
  meets_data = []
  for meet in meets:
    meets_data.append({
      "id": meet.id,
      "meet_date": str(meet.meet_date),
      "meet_type": meet.meet_type,
      "title": meet.title,
      "description": meet.description,
      "location": meet.location,
      "start_time": str(meet.start_time) if meet.start_time else None,
      "end_time": str(meet.end_time) if meet.end_time else None,
      "status": meet.status,
      "is_mandatory": meet.is_mandatory,
      "total_neighbors": meet.total_neighbors,
      "total_present": meet.total_present,
      "total_absent": meet.total_absent,
      "total_on_time": meet.total_on_time,
      "organizer": meet.organizer,
      "notes": meet.notes,
      "created_at": str(meet.created_at),
      "updated_at": str(meet.updated_at)
    })

  return meets_data


@router.get("/{meet_id}", response_model=schemas.Meet)
def read_meet(meet_id: int, db: Session = Depends(get_db)):
  """
  Obtiene una reunión específica
  """
  meet = crud.get_meet(db, meet_id=meet_id)
  if meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  return {
    "id": meet.id,
    "meet_date": str(meet.meet_date),
    "meet_type": meet.meet_type,
    "title": meet.title,
    "description": meet.description,
    "location": meet.location,
    "start_time": str(meet.start_time) if meet.start_time else None,
    "end_time": str(meet.end_time) if meet.end_time else None,
    "status": meet.status,
    "is_mandatory": meet.is_mandatory,
    "total_neighbors": meet.total_neighbors,
    "total_present": meet.total_present,
    "total_absent": meet.total_absent,
    "total_on_time": meet.total_on_time,
    "organizer": meet.organizer,
    "notes": meet.notes,
    "created_at": str(meet.created_at),
    "updated_at": str(meet.updated_at)
  }


@router.post("/", response_model=schemas.Meet)
def create_meet(meet: schemas.MeetCreate, db: Session = Depends(get_db)):
  """
  Crea una nueva reunión
  """
  db_meet = crud.create_meet(db=db, meet=meet)

  return {
    "id": db_meet.id,
    "meet_date": str(db_meet.meet_date),
    "meet_type": db_meet.meet_type,
    "title": db_meet.title,
    "description": db_meet.description,
    "location": db_meet.location,
    "start_time": str(db_meet.start_time) if db_meet.start_time else None,
    "end_time": str(db_meet.end_time) if db_meet.end_time else None,
    "status": db_meet.status,
    "is_mandatory": db_meet.is_mandatory,
    "total_neighbors": db_meet.total_neighbors,
    "total_present": db_meet.total_present,
    "total_absent": db_meet.total_absent,
    "total_on_time": db_meet.total_on_time,
    "organizer": db_meet.organizer,
    "notes": db_meet.notes,
    "created_at": str(db_meet.created_at),
    "updated_at": str(db_meet.updated_at)
  }


@router.put("/{meet_id}", response_model=schemas.Meet)
def update_meet(meet_id: int, meet: schemas.MeetUpdate, db: Session = Depends(get_db)):
  """
  Actualiza una reunión existente
  """
  db_meet = crud.update_meet(db, meet_id=meet_id, meet=meet)
  if db_meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  return {
    "id": db_meet.id,
    "meet_date": str(db_meet.meet_date),
    "meet_type": db_meet.meet_type,
    "title": db_meet.title,
    "description": db_meet.description,
    "location": db_meet.location,
    "start_time": str(db_meet.start_time) if db_meet.start_time else None,
    "end_time": str(db_meet.end_time) if db_meet.end_time else None,
    "status": db_meet.status,
    "is_mandatory": db_meet.is_mandatory,
    "total_neighbors": db_meet.total_neighbors,
    "total_present": db_meet.total_present,
    "total_absent": db_meet.total_absent,
    "total_on_time": db_meet.total_on_time,
    "organizer": db_meet.organizer,
    "notes": db_meet.notes,
    "created_at": str(db_meet.created_at),
    "updated_at": str(db_meet.updated_at)
  }


@router.delete("/{meet_id}")
def delete_meet(meet_id: int, db: Session = Depends(get_db)):
  """
  Elimina una reunión
  """
  success = crud.delete_meet(db, meet_id=meet_id)
  if not success:
    raise HTTPException(status_code=404, detail="Meet not found")
  return {"message": "Meet deleted successfully", "id": meet_id}


@router.get("/{meet_id}/assistances")
def read_meet_assistances(meet_id: int, db: Session = Depends(get_db)):
  """
  Obtiene todas las asistencias de una reunión específica
  """
  # Verificar que la reunión existe
  meet = crud.get_meet(db, meet_id=meet_id)
  if meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  assistances = crud.get_meet_assistances(db, meet_id=meet_id)

  # Formatear respuesta con datos del vecino
  assistances_data = []
  for assistance in assistances:
    neighbor = assistance.neighbor
    neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

    assistances_data.append({
      "id": assistance.id,
      "meet_id": assistance.meet_id,
      "neighbor_id": assistance.neighbor_id,
      "neighbor_name": neighbor_name,
      "is_present": assistance.is_present,
      "is_on_time": assistance.is_on_time,
      "arrival_time": str(assistance.arrival_time) if assistance.arrival_time else None,
      "departure_time": str(assistance.departure_time) if assistance.departure_time else None,
      "excuse_reason": assistance.excuse_reason,
      "has_excuse": assistance.has_excuse,
      "represented_by": assistance.represented_by,
      "has_representative": assistance.has_representative,
      "notes": assistance.notes
    })

  return assistances_data


@router.post("/{meet_id}/assistances", response_model=schemas.Assistance)
def create_meet_assistance(meet_id: int, assistance: schemas.AssistanceBase, db: Session = Depends(get_db)):
  """
  Crea un registro de asistencia para una reunión
  """
  # Verificar que la reunión existe
  meet = crud.get_meet(db, meet_id=meet_id)
  if meet is None:
    raise HTTPException(status_code=404, detail="Meet not found")

  # Crear el schema con meet_id
  assistance_create = schemas.AssistanceCreate(
    meet_id=meet_id,
    neighbor_id=assistance.neighbor_id,
    is_present=assistance.is_present,
    is_on_time=assistance.is_on_time
  )

  db_assistance = crud.create_assistance(db=db, assistance=assistance_create)

  # Obtener nombre del vecino para la respuesta
  neighbor = db_assistance.neighbor
  neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

  return {
    "id": db_assistance.id,
    "meet_id": db_assistance.meet_id,
    "neighbor_id": db_assistance.neighbor_id,
    "neighbor_name": neighbor_name,
    "is_present": db_assistance.is_present,
    "is_on_time": db_assistance.is_on_time,
    "arrival_time": str(db_assistance.arrival_time) if db_assistance.arrival_time else None,
    "departure_time": str(db_assistance.departure_time) if db_assistance.departure_time else None,
    "excuse_reason": db_assistance.excuse_reason,
    "has_excuse": db_assistance.has_excuse,
    "represented_by": db_assistance.represented_by,
    "has_representative": db_assistance.has_representative,
    "notes": db_assistance.notes
  }


@router.put("/{assistance_id}", response_model=schemas.Assistance)
def update_assistance(assistance_id: int, assistance: schemas.AssistanceUpdate, db: Session = Depends(get_db)):
  """
  Actualiza un registro de asistencia
  """
  db_assistance = crud.update_assistance(db, assistance_id=assistance_id, assistance=assistance)
  if db_assistance is None:
    raise HTTPException(status_code=404, detail="Assistance not found")

  # Obtener nombre del vecino para la respuesta
  neighbor = db_assistance.neighbor
  neighbor_name = f"{neighbor.first_name} {neighbor.second_name or ''} {neighbor.last_name}".strip()

  return {
    "id": db_assistance.id,
    "meet_id": db_assistance.meet_id,
    "neighbor_id": db_assistance.neighbor_id,
    "neighbor_name": neighbor_name,
    "is_present": db_assistance.is_present,
    "is_on_time": db_assistance.is_on_time,
    "arrival_time": str(db_assistance.arrival_time) if db_assistance.arrival_time else None,
    "departure_time": str(db_assistance.departure_time) if db_assistance.departure_time else None,
    "excuse_reason": db_assistance.excuse_reason,
    "has_excuse": db_assistance.has_excuse,
    "represented_by": db_assistance.represented_by,
    "has_representative": db_assistance.has_representative,
    "notes": db_assistance.notes
  }


@router.post("/{meet_id}/recalculate-statistics")
def recalculate_meet_statistics(meet_id: int, db: Session = Depends(get_db)):
  """
  Recalcula las estadísticas de asistencia de una reunión
  """
  meet = crud.update_meet_statistics(db, meet_id)
  if not meet:
    raise HTTPException(status_code=404, detail="Meet not found")

  return {
    "message": "Statistics updated successfully",
    "total_neighbors": meet.total_neighbors,
    "total_present": meet.total_present,
    "total_absent": meet.total_absent,
    "total_on_time": meet.total_on_time
  }


@router.post("/recalculate-all-statistics")
def recalculate_all_meets_statistics(db: Session = Depends(get_db)):
  """
  Recalcula las estadísticas de asistencia de todas las reuniones
  """
  meets = crud.get_meets(db)
  updated_count = 0

  for meet in meets:
    crud.update_meet_statistics(db, meet.id)
    updated_count += 1

  return {
    "message": f"Statistics updated successfully for {updated_count} meetings",
    "updated_count": updated_count
  }
