from fastapi import APIRouter, Depends, Security
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from app.database import get_db
from sqlalchemy.orm import Session
from app import models, schemas
from typing import List
from app.utils import get, create, edit, delete, APIException
from PIL import Image
from app.routers.storybuilders.utils import (
    generate_recto_card,
    generate_verso_card,
    generate_card_prints,
)
import io
import os
import datetime
import tarfile

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
    # Invalid card images
    for card in datas:
        if os.path.isfile(
            f"./app/routers/storybuilders/generated/cards/card_{card.id}_0.png"
        ):
            os.remove(
                f"./app/routers/storybuilders/generated/cards/card_{card.id}_0.png"
            )
        if os.path.isfile(
            f"./app/routers/storybuilders/generated/cards/card_{card.id}_1.png"
        ):
            os.remove(
                f"./app/routers/storybuilders/generated/cards/card_{card.id}_1.png"
            )
    return edit(db, models.Card, datas, "id")


@router.post("/delete", response_model=schemas.DefaultResponse)
async def delete_card(payload: schemas.DeleteId, db: Session = Depends(get_db)):
    data = payload.dict()
    card_id = data["id"]
    # Delete card images
    if os.path.isfile(
        f"./app/routers/storybuilders/generated/cards/card_{card_id}_0.png"
    ):
        os.remove(f"./app/routers/storybuilders/generated/cards/card_{card_id}_0.png")
    if os.path.isfile(
        f"./app/routers/storybuilders/generated/cards/card_{card_id}_1.png"
    ):
        os.remove(f"./app/routers/storybuilders/generated/cards/card_{card_id}_1.png")
    return delete(db, models.Card, (models.Card.id == card_id))


def get_or_create_card_image(card, card_type, face, card_id):
    if os.path.isfile(
        f"./app/routers/storybuilders/generated/cards/card_{card_id}_{face}.png"
    ):
        f = open(
            f"./app/routers/storybuilders/generated/cards/card_{card_id}_{face}.png",
            "rb",
        )
        return f
    if face == 0:
        card_img = generate_recto_card(card, card_type)
    else:
        card_img = generate_verso_card(card, card_type)

    card_bytes = io.BytesIO()
    card_img.save(
        f"./app/routers/storybuilders/generated/cards/card_{card_id}_{face}.png", "png"
    )
    card_img.save(card_bytes, "png")
    card_bytes.seek(0)
    return card_bytes


@router.get("/image/{card_id}/{face}", response_class=StreamingResponse)
def get_image(card_id: int, face: int, db: Session = Depends(get_db)):
    card, card_type = (
        db.query(models.Card, models.CardType)
        .join(models.CardType)
        .filter(models.Card.id == card_id)
        .first()
    )
    data = get_or_create_card_image(card, card_type, face, card_id)
    return StreamingResponse(data, media_type="image/png")


@router.get("/generate_print/{start_id}/{end_id}", response_class=FileResponse)
async def generate_print(start_id: int, end_id: int, db: Session = Depends(get_db)):
    i = start_id
    card_prints = []
    while i <= end_id:
        # print(i, (i + 11 if i + 11 < end_id else end_id))
        card_prints.append(
            generate_card_prints(i, (i + 11 if i + 11 < end_id else end_id), db)
        )
        i = i + 11
    f_name = f"./app/routers/storybuilders/generated/generated_prints_{start_id}_{end_id}_{datetime.datetime.now().timestamp()}.tar.gz"
    tar = tarfile.open(
        f_name,
        "w:gz",
    )
    for filename in card_prints:
        recto = open(filename[0][1], "rb")
        recto_tar_info = tarfile.TarInfo(filename[0][0])
        recto_tar_info.size = os.path.getsize(filename[0][1])
        tar.addfile(recto_tar_info, recto)
        verso = open(filename[1][1], "rb")
        verso_tar_info = tarfile.TarInfo(filename[1][0])
        verso_tar_info.size = os.path.getsize(filename[1][1])
        tar.addfile(verso_tar_info, verso)
    tar.close()
    f = open(
        f_name,
        "rb",
    )
    response = StreamingResponse(f, media_type="application/x-tgz")
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename=generated_prints_{start_id}_{end_id}.tar.gz"
    return response
