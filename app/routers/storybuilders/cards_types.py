from fastapi import APIRouter, Depends, Security
from fastapi.responses import JSONResponse, StreamingResponse
from app.database import get_db, Base
from sqlalchemy.orm import Session
from app import models, schemas
from app.utils import get, create, edit, delete, APIException
from app.routers.storybuilders.utils import (
    generate_recto_card,
    generate_verso_card,
)
from random import randrange
import io

router = APIRouter()


# Types


@router.get("/get", response_model=schemas.CardTypeResponseCollection)
def get_card_types(db: Session = Depends(get_db)):
    return {"__root__": get(db, models.CardType, models.CardType.id)}


@router.post("/create", response_model=schemas.CardTypeResponseCollection)
async def create_card_type(
    payload: schemas.CardTypeCollection, db: Session = Depends(get_db)
):
    try:
        return create(db, models.CardType, payload.dict())
    except APIException as e:
        db.rollback()
        return JSONResponse(
            status_code=411,
            content={
                "message": "An error occured : '{}' type already exist.".format(
                    e.item["name"]
                )
            },
        )


@router.post("/edit", response_model=schemas.CardTypeResponseCollection)
async def edit_card(
    payload: schemas.CardTypeResponseCollection, db: Session = Depends(get_db)
):
    data = payload.dict()
    print(data)
    return edit(db, models.CardType, data, "id")


@router.post("/delete", response_model=schemas.DefaultResponse)
async def delete_card(payload: schemas.DeleteId, db: Session = Depends(get_db)):
    data = payload.dict()
    return delete(db, models.CardType, (models.CardType.id == data["id"]))


@router.get("/image/{type_id}/{face}", response_class=StreamingResponse)
def get_image(type_id: int, face: int, db: Session = Depends(get_db)):
    card_type = db.query(models.CardType).filter(models.CardType.id == type_id).first()
    template_card = models.Card(name="Template", difficulty=randrange(1, 5))
    if face == 0:
        card_type_img = generate_recto_card(template_card, card_type)
    else:
        card_type_img = generate_verso_card(template_card, card_type)

    card_type_bytes = io.BytesIO()
    card_type_img.save(card_type_bytes, "png", dpi=(300, 300))
    card_type_bytes.seek(0)
    return StreamingResponse(card_type_bytes, media_type="image/png")
