from fastapi import APIRouter, Depends, Security
from fastapi.responses import JSONResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app import models, schemas
from typing import List
from app.utils import get, create, edit, delete, APIException


router = APIRouter()


@router.get("/get", response_model=schemas.ExtensionResponseCollection)
def get_cards_extension(
    db: Session = Depends(get_db),
):
    return {"__root__": get(db, models.CardExtension)}


@router.post(
    "/create",
    response_model=schemas.ExtensionResponseCollection,
    responses={411: {"model": schemas.DefaultResponse}},
)
async def create_card_extension(
    payload: schemas.ExtensionBaseCollection,
    db: Session = Depends(get_db),
):
    try:
        return {"__root__": create(db, models.CardExtension, payload.dict())}
    except APIException as e:
        db.rollback()
        return JSONResponse(
            status_code=411,
            content={
                "message": "An error occured : '{}' extension already exist.".format(
                    e.item["name"]
                )
            },
        )


@router.post("/edit", response_model=schemas.ExtensionResponseCollection)
async def edit_card(
    payload: schemas.ExtensionResponseCollection, db: Session = Depends(get_db)
):
    data = payload.dict()
    return edit(db, models.CardExtension, data, "id")


@router.post("/delete", response_model=schemas.DefaultResponse)
async def delete_card(payload: schemas.DeleteId, db: Session = Depends(get_db)):
    data = payload.dict()
    return delete(db, models.CardExtension, (models.CardExtension.id == data["id"]))
