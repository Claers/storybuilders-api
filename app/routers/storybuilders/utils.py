from PIL import Image, ImageDraw, ImageFont, ImageColor
from PIL.ImageChops import difference
from sqlalchemy.orm import Session
import numpy as np
from app import models


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def change_color(img, type_color, r=32, g=32, b=32):
    data = np.array(img)  # "data" is a height x width x 4 numpy array
    red, green, blue, alpha = data.T  # Temporarily unpack the bands for readability

    # Replace white with red... (leaves alpha values alone...)
    white_areas = (red == r) & (blue == g) & (green == b)
    data[..., :-1][white_areas.T] = type_color  # Transpose back needed

    return Image.fromarray(data)


def generate_type_card(card_type):
    card = Image.new(mode="RGB", size=(400, 400), color=(255, 255, 255, 255))
    contour = Image.open("./app/routers/storybuilders/assets/Contour.png")
    if card_type.color:
        contour = change_color(contour, ImageColor.getrgb(card_type.color))
    card.paste(contour, (0, 0))
    return card


def generate_difficulty(difficulty, card_type):
    difficulty_img = Image.open("./app/routers/storybuilders/assets/Difficulty10X.png")
    difficulty_img_w, difficulty_img_h = difficulty_img.size
    difficulty_img = change_color(
        difficulty_img, ImageColor.getrgb(card_type.color), 255, 255, 255
    )
    difficulty_total = Image.new(
        mode="RGB",
        size=((difficulty_img_w) * difficulty, difficulty_img_h),
        color=(255, 255, 255, 0),
    )
    for i in range(0, difficulty):
        difficulty_total.paste(
            difficulty_img, ((difficulty_img_w) * i, 0), difficulty_img
        )
    difficulty_total = difficulty_total.resize(
        (int((difficulty_img_w + 10) * difficulty / 4), int(difficulty_img_h / 4))
    )
    return difficulty_total


def create_card_text(text, draw, font, card_w, card_h, iterator=0):
    right = 100 + draw.textlength(text, font=font)
    print(right < card_w)
    if right < card_w:

        return
    texts = [
        text[: int(len(text) / 2)],
        text[int(len(text) / 2) :],
    ]
    i = iterator
    for t in texts:
        create_card_text(t, draw, font, card_w, card_h, i)
        i += 1


def generate_recto_card(card, card_type):
    # Card canvas
    card_img = generate_type_card(card_type)
    # Card type
    font_title = ImageFont.truetype(
        "./app/routers/storybuilders/assets/fonts/Chewy-Regular.ttf", 34
    )
    font_text = ImageFont.truetype(
        "./app/routers/storybuilders/assets/fonts/Chewy-Regular.ttf", 29
    )
    draw = ImageDraw.Draw(card_img)
    card_w, card_h = card_img.size
    _, _, type_box_w, _ = draw.textbbox((0, 0), card_type.name, font=font_title)
    draw.text(
        ((card_w - type_box_w) / 2, 20),
        card_type.name,
        (0, 0, 0),
        font=font_title,
    )
    # Separator 1
    separator = Image.open("./app/routers/storybuilders/assets/CardSeparator2X.png")
    separator_w, separator_h = separator.size
    separator = separator.resize((separator_w + 45, separator_h))
    separator_w, separator_h = separator.size
    separator_offset = (int(card_w / 2) - int(separator_w / 2), 25 + separator_h + 30)
    card_img.paste(separator, separator_offset, separator)
    # Card Text
    # create_card_text(card.name.replace("\\n", "\n"), draw, font, card_w, card_h)
    _, _, text_box_w, text_box_h = draw.textbbox(
        (0, 40), card.name.replace("\\n", "\n"), font=font_text
    )
    draw.text(
        (
            50,
            85,
        ),
        card.name.replace("\\n", "\n").strip(),
        (0, 0, 0),
        font=font_text,
    )
    # Card Difficulty
    difficulty_img = generate_difficulty(card.difficulty, card_type)
    _, difficulty_img_h = difficulty_img.size
    card_img.paste(
        generate_difficulty(card.difficulty, card_type),
        (int(card_w / 5) + 20, card_h - difficulty_img_h - 20),
    )
    return card_img


def generate_verso_card(card, card_type):
    # Card canvas
    card_img = generate_type_card(card_type)
    logo = Image.open("./app/routers/storybuilders/assets/Logo2X.png")
    logo_w, logo_h = logo.size
    img_offset = (15, (400 - logo_h) // 2)
    card_img.paste(logo, img_offset, logo)
    font = ImageFont.truetype(
        "./app/routers/storybuilders/assets/fonts/Chewy-Regular.ttf", 45
    )
    # Type Text
    draw = ImageDraw.Draw(card_img)
    card_w, card_h = card_img.size
    _, _, w, h = draw.textbbox((0, 0), card_type.name, font=font)
    draw.text(
        ((card_w - w) / 2, (card_h - h) / 3 - 20),
        card_type.name,
        (0, 0, 0),
        font=font,
    )
    # Card Difficulty
    difficulty_img = generate_difficulty(card.difficulty, card_type)
    _, difficulty_img_h = difficulty_img.size
    card_img.paste(
        generate_difficulty(card.difficulty, card_type),
        (int(card_w / 5) + 20, card_h - difficulty_img_h - int(card_h / 4)),
    )
    return card_img


anchors_recto = {
    1: (int(1691 / 4) * 1 - 400, 50),
    2: (int(1691 / 4) * 2 - 400, 50),
    3: (int(1691 / 4) * 3 - 400, 50),
    4: (int(1691 / 4) * 4 - 400, 50),
    5: (int(1691 / 4) * 1 - 400, 50 + int(2178 / 4) * 1),
    6: (int(1691 / 4) * 2 - 400, 50 + int(2178 / 4) * 1),
    7: (int(1691 / 4) * 3 - 400, 50 + int(2178 / 4) * 1),
    8: (int(1691 / 4) * 4 - 400, 50 + int(2178 / 4) * 1),
    9: (int(1691 / 4) * 1 - 400, 50 + int(2178 / 4) * 2),
    10: (int(1691 / 4) * 2 - 400, 50 + int(2178 / 4) * 2),
    11: (int(1691 / 4) * 3 - 400, 50 + int(2178 / 4) * 2),
    12: (int(1691 / 4) * 4 - 400, 50 + int(2178 / 4) * 2),
    13: (int(1691 / 4) * 1 - 400, 50 + int(2178 / 4) * 3),
    14: (int(1691 / 4) * 2 - 400, 50 + int(2178 / 4) * 3),
    15: (int(1691 / 4) * 3 - 400, 50 + int(2178 / 4) * 3),
    16: (int(1691 / 4) * 4 - 400, 50 + int(2178 / 4) * 3),
}

anchors_verso = {
    1: (1691 - int(1691 / 4) * 1, 50),
    2: (1691 - int(1691 / 4) * 2, 50),
    3: (1691 - int(1691 / 4) * 3, 50),
    4: (1691 - int(1691 / 4) * 4, 50),
    5: (1691 - int(1691 / 4) * 1, 50 + int(2178 / 4) * 1),
    6: (1691 - int(1691 / 4) * 2, 50 + int(2178 / 4) * 1),
    7: (1691 - int(1691 / 4) * 3, 50 + int(2178 / 4) * 1),
    8: (1691 - int(1691 / 4) * 4, 50 + int(2178 / 4) * 1),
    9: (1691 - int(1691 / 4) * 1, 50 + int(2178 / 4) * 2),
    10: (1691 - int(1691 / 4) * 2, 50 + int(2178 / 4) * 2),
    11: (1691 - int(1691 / 4) * 3, 50 + int(2178 / 4) * 2),
    12: (1691 - int(1691 / 4) * 4, 50 + int(2178 / 4) * 2),
    13: (1691 - int(1691 / 4) * 1, 50 + int(2178 / 4) * 3),
    14: (1691 - int(1691 / 4) * 2, 50 + int(2178 / 4) * 3),
    15: (1691 - int(1691 / 4) * 3, 50 + int(2178 / 4) * 3),
    16: (1691 - int(1691 / 4) * 4, 50 + int(2178 / 4) * 3),
}


def generate_card_prints(start_id, end_id, db):
    recto_name = f"./app/routers/storybuilders/generated/prints/cards_{start_id}_{end_id}_recto.jpeg"
    verso_name = f"./app/routers/storybuilders/generated/prints/cards_{start_id}_{end_id}_verso.jpeg"
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
    return (
        (
            f"cards_{start_id}_{end_id}_recto.jpeg",
            f"./app/routers/storybuilders/generated/prints/cards_{start_id}_{end_id}_recto.jpeg",
        ),
        (
            f"cards_{start_id}_{end_id}_verso.jpeg",
            f"./app/routers/storybuilders/generated/prints/cards_{start_id}_{end_id}_verso.jpeg",
        ),
    )
