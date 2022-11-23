from PIL import Image, ImageDraw, ImageFont, ImageColor
from PIL.ImageChops import difference
from sqlalchemy.orm import Session
import numpy as np
import svgutils.transform as sg


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


def generate_svg_card(card_type):
    svg_card = sg.SVGFigure(400, 400)
    contour = sg.fromfile("./app/routers/storybuilders/assets/Contour.svg").getroot()
    contour.moveto(100, 100)
    svg_card.append(contour)
    return svg_card


def generate_svg_recto_card(card, card_type):
    svg_card = generate_svg_card(card_type)
    return svg_card


def generate_svg_verso_card(card, card_type):
    svg_card = generate_svg_card(card_type)
    return svg_card


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
    font = ImageFont.truetype(
        "./app/routers/storybuilders/assets/fonts/Chewy-Regular.ttf", 24
    )
    draw = ImageDraw.Draw(card_img)
    card_w, card_h = card_img.size
    _, _, type_box_w, _ = draw.textbbox((0, 0), card_type.name, font=font)
    draw.text(
        ((card_w - type_box_w) / 2, 20),
        card_type.name,
        (0, 0, 0),
        font=font,
    )
    # Separator 1
    separator = Image.open("./app/routers/storybuilders/assets/CardSeparator2X.png")
    separator_w, separator_h = separator.size
    separator = separator.resize((separator_w + 45, separator_h))
    separator_w, separator_h = separator.size
    separator_offset = (int(card_w / 2) - int(separator_w / 2), 20 + separator_h + 30)
    card_img.paste(separator, separator_offset, separator)
    # Card Text
    # create_card_text(card.name.replace("\\n", "\n"), draw, font, card_w, card_h)
    _, _, text_box_w, text_box_h = draw.textbbox(
        (0, 40), card.name.replace("\\n", "\n"), font=font
    )
    draw.text(
        (
            50,
            80,
        ),
        card.name.replace("\\n", "\n").strip(),
        (0, 0, 0),
        font=font,
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
        "./app/routers/storybuilders/assets/fonts/Chewy-Regular.ttf", 40
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
    return card_img
