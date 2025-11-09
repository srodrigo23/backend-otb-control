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