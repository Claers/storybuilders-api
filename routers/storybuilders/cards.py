from fastapi import APIRouter, Depends, Security
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app import models, schemas
from typing import List
from app.utils import get, create, edit, delete, APIException
from PIL import Image
from app.routers.storybuilders.utils import generate_recto_card, generate_verso_card
import io

router = APIRouter()

# Cards


@router.get("/get", response_model=schemas.CardCollection)
def get_cards(
    db: Session = Depends(get_db),
):
    return {"__root__": get(db, models.Card, models.Card.id)}


@router.post(
    "/create",
    response_model=schemas.CardCollection,
    responses={401: {"model": schemas.DefaultResponse}},
)
async def create_card(
    payload: schemas.CardBaseCollection,
    db: Session = Depends(get_db),
):
    try:
        return {"__root__": create(db, models.Card, payload.dict())}
    except APIException as e:
        db.rollback()
        return JSONResponse(
            status_code=401,
            content={
                "message": "An error occured : '{}' card already exist.".format(
                    e.item["name"]
                )
            },
        )


@router.post("/edit", response_model=schemas.CardCollection)
async def edit_card(payload: schemas.CardCollection, db: Session = Depends(get_db)):
    datas = payload.dict()
    print(datas)
    return edit(db, models.Card, datas, "id")


@router.post("/delete", response_model=schemas.DefaultResponse)
async def delete_card(payload: schemas.DeleteId, db: Session = Depends(get_db)):
    data = payload.dict()
    return delete(db, models.Card, (models.Card.id == data["id"]))


@router.get("/image/{card_id}/{face}", response_class=StreamingResponse)
def get_image(card_id: int, face: int, db: Session = Depends(get_db)):
    card, card_type = (
        db.query(models.Card, models.CardType)
        .join(models.CardType)
        .filter(models.Card.id == card_id)
        .first()
    )
    if face == 0:
        card_img = generate_recto_card(card, card_type)
    else:
        card_img = generate_verso_card(card, card_type)

    card_bytes = io.BytesIO()
    card_img.save(card_bytes, "png")
    card_bytes.seek(0)
    return StreamingResponse(card_bytes, media_type="image/png")


anchors_recto = {
    1: (int(1691 / 4) * 1 - 400, 10),
    2: (int(1691 / 4) * 2 - 400, 10),
    3: (int(1691 / 4) * 3 - 400, 10),
}

anchors_verso = {
    1: (1691 - int(1691 / 4) * 1, 10),
    2: (1691 - int(1691 / 4) * 2, 10),
    3: (1691 - int(1691 / 4) * 3, 10),
}


@router.get("/generate_print/{start_id}/{end_id}", response_class=FileResponse)
async def generate_print(start_id: int, end_id: int, db: Session = Depends(get_db)):
    recto_name = (
        f"./app/routers/storybuilders/generated/cards_{start_id}_{end_id}_recto.jpeg"
    )
    verso_name = (
        f"./app/routers/storybuilders/generated/cards_{start_id}_{end_id}_verso.jpeg"
    )
    # Planche d'impression
    recto = Image.new(mode="RGBA", size=(1691, 2178), color=(255, 255, 255))
    verso = Image.new(mode="RGBA", size=(1691, 2178), color=(255, 255, 255))
    # Get data
    cards = (
        db.query(models.Card, models.CardType, models.CardExtension)
        .join(models.CardType, models.CardExtension)
        .filter(models.Card.id >= start_id, models.Card.id <= end_id)
        .all()
    )
    i = 0
    for card in cards:
        i += 1
        verso.paste(generate_verso_card(card[0], card[1]), anchors_verso[i])
        recto.paste(generate_recto_card(card[0], card[1]), anchors_recto[i])

    recto.convert("CMYK").save(recto_name)
    verso.convert("CMYK").save(verso_name)
