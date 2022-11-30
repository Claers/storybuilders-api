from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


class APIException(Exception):
    def __init__(self, item: object) -> None:
        self.item = item
        super().__init__()


def get(db: Session, model: models.CustomBase, order_by=None, filter_by=None):
    query = db.query(model)
    if order_by:
        query = query.order_by(order_by)
    if filter_by:
        query = query.filter(filter_by)
    datas: List[models.CustomBase] = query.all()
    return [data.to_dict() for data in datas]


def create(db: Session, model, datas):
    new_items = []
    for data in datas["__root__"]:
        new_item = model(**data)
        new_items.append(new_item)
        db.add(new_item)
        try:
            db.flush()
        except Exception as e:
            print(e.args)
            print(e)
            raise APIException(data)
    db.commit()
    map(lambda new_item: db.refresh(new_item), new_items)
    return new_items


def edit(db: Session, model: models.CustomBase, datas, filter_field):
    items = []
    for data in datas["__root__"]:
        filter_by = object.__getattribute__(model, filter_field) == data[filter_field]
        item: models.CustomBase = db.query(model).filter(filter_by).first()
        if item.to_dict() != data:
            item.update(data)
            items.append(item)
            try:
                db.flush()
            except:
                raise APIException(data)
    db.commit()
    map(lambda new_item: db.refresh(new_item), items)
    return {"__root__": items}


def delete(db: Session, model: models.CustomBase, filter_by):
    item = db.query(model).filter(filter_by).first()
    db.delete(item)
    db.commit()
    return {"message": "Deleted"}
