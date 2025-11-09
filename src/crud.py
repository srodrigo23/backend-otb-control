from sqlalchemy.orm import Session

import models, schemas


def get_neighbor(db: Session, neighbor_id: int):
    return db.query(models.Neighbor).filter(models.Neighbor.id == neighbor_id).first()


def get_neighbor_by_email(db: Session, email: str):
    return db.query(models.Neighbor).filter(models.Neighbor.email == email).first()


def get_neighbors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Neighbor).all()
        #.offset(skip).limit(limit)


def create_neighbor(db: Session, neighbor: schemas.NeighborCreate):
    db_neighbor = models.Neighbor(
        first_name=neighbor.first_name,
        second_name=neighbor.second_name or "",
        last_name=neighbor.last_name,
        ci=neighbor.ci,
        phone_number=str(neighbor.phone_number),
        email=neighbor.email
    )
    db.add(db_neighbor)
    db.commit()
    db.refresh(db_neighbor)
    return db_neighbor


def get_neighbor_meters(db: Session, neighbor_id: int):
    """Obtiene todos los medidores de un vecino"""
    return db.query(models.NeighborMeter).filter(models.NeighborMeter.neighbor_id == neighbor_id).all()


def get_neighbor_payments(db: Session, neighbor_id: int):
    """Obtiene todos los pagos de un vecino ordenados por fecha descendente"""
    return db.query(models.Payment).filter(
        models.Payment.neighbor_id == neighbor_id
    ).order_by(models.Payment.payment_date.desc()).all()


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.model_dump(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_neighbor(db: Session, neighbor_id: int, neighbor: schemas.NeighborUpdate):
    db_neighbor = db.query(models.Neighbor).filter(models.Neighbor.id == neighbor_id).first()
    if db_neighbor:
        update_data = neighbor.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_neighbor, key, value)
        db.commit()
        db.refresh(db_neighbor)
    return db_neighbor


def delete_neighbor(db: Session, neighbor_id: int):
    db_neighbor = db.query(models.Neighbor).filter(models.Neighbor.id == neighbor_id).first()
    if db_neighbor:
        db.delete(db_neighbor)
        db.commit()
        return True
    return False


# ========== DEUDAS ==========

def get_neighbor_active_debts(db: Session, neighbor_id: int):
    """
    Obtiene todas las deudas activas (pending, partial, overdue) de un vecino
    """
    debts = db.query(models.DebtItem).filter(
        models.DebtItem.neighbor_id == neighbor_id,
        models.DebtItem.status.in_(["pending", "partial", "overdue"])
    ).all()

    return debts


def get_neighbor_all_debts(db: Session, neighbor_id: int):
    """
    Obtiene todas las deudas de un vecino (incluyendo pagadas)
    """
    debts = db.query(models.DebtItem).filter(
        models.DebtItem.neighbor_id == neighbor_id
    ).all()

    return debts


def get_debt_item(db: Session, debt_id: int):
    """
    Obtiene una deuda específica por ID
    """
    return db.query(models.DebtItem).filter(models.DebtItem.id == debt_id).first()


# ========== MEDICIONES ==========

def get_measures(db: Session):
    """
    Obtiene todas las mediciones ordenadas por fecha de creación (más recientes primero)
    """
    return db.query(models.Measure).order_by(models.Measure.created_at.desc()).all()


def get_measure(db: Session, measure_id: int):
    """
    Obtiene una medición específica por ID
    """
    return db.query(models.Measure).filter(models.Measure.id == measure_id).first()


def create_measure(db: Session, measure: schemas.MeasureCreate):
    """
    Crea una nueva medición
    """
    from datetime import datetime

    # Convertir la fecha de string a objeto Date
    measure_date = datetime.strptime(measure.measure_date, "%Y-%m-%d").date()

    db_measure = models.Measure(
        measure_date=measure_date,
        period=measure.period,
        reader_name=measure.reader_name,
        notes=measure.notes,
        status="in_progress",
        total_meters=0,
        meters_read=0,
        meters_pending=0
    )
    db.add(db_measure)
    db.commit()
    db.refresh(db_measure)
    return db_measure


def update_measure(db: Session, measure_id: int, measure: schemas.MeasureUpdate):
    """
    Actualiza una medición existente
    """
    db_measure = db.query(models.Measure).filter(models.Measure.id == measure_id).first()
    if db_measure:
        update_data = measure.model_dump(exclude_unset=True)

        # Si se actualiza la fecha, convertirla
        if "measure_date" in update_data and update_data["measure_date"]:
            from datetime import datetime
            update_data["measure_date"] = datetime.strptime(update_data["measure_date"], "%Y-%m-%d").date()

        for key, value in update_data.items():
            setattr(db_measure, key, value)
        db.commit()
        db.refresh(db_measure)
    return db_measure


def delete_measure(db: Session, measure_id: int):
    """
    Elimina una medición
    """
    db_measure = db.query(models.Measure).filter(models.Measure.id == measure_id).first()
    if db_measure:
        db.delete(db_measure)
        db.commit()
        return True
    return False


# ========== REUNIONES ==========

def get_meets(db: Session):
    """
    Obtiene todas las reuniones ordenadas por fecha de creación (más recientes primero)
    """
    return db.query(models.Meet).order_by(models.Meet.created_at.desc()).all()


def get_meet(db: Session, meet_id: int):
    """
    Obtiene una reunión específica por ID
    """
    return db.query(models.Meet).filter(models.Meet.id == meet_id).first()


def create_meet(db: Session, meet: schemas.MeetCreate):
    """
    Crea una nueva reunión
    """
    from datetime import datetime

    # Convertir la fecha de string a objeto DateTime
    meet_date = datetime.strptime(meet.meet_date, "%Y-%m-%dT%H:%M")

    db_meet = models.Meet(
        meet_date=meet_date,
        meet_type=meet.meet_type,
        title=meet.title,
        description=meet.description,
        location=meet.location,
        is_mandatory=meet.is_mandatory,
        organizer=meet.organizer,
        notes=meet.notes,
        status="scheduled",
        total_neighbors=0,
        total_present=0,
        total_absent=0,
        total_on_time=0
    )
    db.add(db_meet)
    db.commit()
    db.refresh(db_meet)
    return db_meet


def update_meet(db: Session, meet_id: int, meet: schemas.MeetUpdate):
    """
    Actualiza una reunión existente
    """
    db_meet = db.query(models.Meet).filter(models.Meet.id == meet_id).first()
    if db_meet:
        update_data = meet.model_dump(exclude_unset=True)

        # Convertir fechas si se proporcionan
        from datetime import datetime
        if "meet_date" in update_data and update_data["meet_date"]:
            update_data["meet_date"] = datetime.strptime(update_data["meet_date"], "%Y-%m-%dT%H:%M")
        if "start_time" in update_data and update_data["start_time"]:
            update_data["start_time"] = datetime.strptime(update_data["start_time"], "%Y-%m-%dT%H:%M")
        if "end_time" in update_data and update_data["end_time"]:
            update_data["end_time"] = datetime.strptime(update_data["end_time"], "%Y-%m-%dT%H:%M")

        for key, value in update_data.items():
            setattr(db_meet, key, value)
        db.commit()
        db.refresh(db_meet)
    return db_meet


def delete_meet(db: Session, meet_id: int):
    """
    Elimina una reunión
    """
    db_meet = db.query(models.Meet).filter(models.Meet.id == meet_id).first()
    if db_meet:
        db.delete(db_meet)
        db.commit()
        return True
    return False


def get_meet_assistances(db: Session, meet_id: int):
    """
    Obtiene todas las asistencias de una reunión específica
    """
    return db.query(models.Assistance).filter(models.Assistance.meet_id == meet_id).all()


def create_assistance(db: Session, assistance: schemas.AssistanceCreate):
    """
    Crea un registro de asistencia
    """
    db_assistance = models.Assistance(
        meet_id=assistance.meet_id,
        neighbor_id=assistance.neighbor_id,
        is_present=assistance.is_present,
        is_on_time=assistance.is_on_time
    )
    db.add(db_assistance)
    db.commit()
    db.refresh(db_assistance)
    return db_assistance


def update_assistance(db: Session, assistance_id: int, assistance: schemas.AssistanceUpdate):
    """
    Actualiza un registro de asistencia
    """
    db_assistance = db.query(models.Assistance).filter(models.Assistance.id == assistance_id).first()
    if db_assistance:
        update_data = assistance.model_dump(exclude_unset=True)

        # Convertir fechas si se proporcionan
        from datetime import datetime
        if "arrival_time" in update_data and update_data["arrival_time"]:
            update_data["arrival_time"] = datetime.strptime(update_data["arrival_time"], "%Y-%m-%dT%H:%M")
        if "departure_time" in update_data and update_data["departure_time"]:
            update_data["departure_time"] = datetime.strptime(update_data["departure_time"], "%Y-%m-%dT%H:%M")

        for key, value in update_data.items():
            setattr(db_assistance, key, value)
        db.commit()
        db.refresh(db_assistance)
    return db_assistance