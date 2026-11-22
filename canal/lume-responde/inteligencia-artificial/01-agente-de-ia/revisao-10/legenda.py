"""Reusa o crescimento de letras da prova da saudação ao longo do episódio."""
from functools import lru_cache
import math

from PIL import ImageDraw, ImageFont

COLOR = "#ffd582"


@lru_cache(maxsize=64)
def face(path, size):
    return ImageFont.truetype(str(path), size)


# Relative growth at the active letter and at offsets of one, two and three.
GROWTH = (.68, .34, .18, .075, 0.0)


def wave(distance):
    if distance >= len(GROWTH) - 1:
        return 0.0
    step = math.floor(distance)
    blend = (1 - math.cos(math.pi * (distance - step))) / 2
    return GROWTH[step] * (1 - blend) + GROWTH[step + 1] * blend


def desenhar(image, path, phrase, marks, time):
    draw = ImageDraw.Draw(image)
    slots = {index: slot for slot, index in enumerate(
        i for i, char in enumerate(phrase) if char.isalpha())}
    highlight = None
    envelope = 0.0
    for first, end, start, stop in marks:
        if start - .035 <= time <= stop + .045:
            phase = max(0, min(1, (time - start) / (stop - start)))
            highlight = slots[first] - .10 + (slots[end-1] - slots[first] + .20) * phase
            edge = min((time - start + .035) / .065, (stop + .045 - time) / .075, 1)
            envelope = (1 - math.cos(math.pi * max(0, edge))) / 2
            break
    sizes = [1 + envelope * wave(abs(slot - highlight))
             if (slot := slots.get(i)) is not None and highlight is not None
             else 1 for i in range(len(phrase))]
    def layout_for(base):
        result = []
        for char, factor in zip(phrase, sizes):
            glyph = face(path, round(base * factor))
            l, _, r, _ = glyph.getbbox(char, anchor="ls")
            width = max(glyph.getlength(char), r - min(0, l) + 4)
            result.append((glyph, width, -min(0, l)))
        return result

    layout = layout_for(108)
    span = sum(width for _, width, _ in layout)
    if span > 980:
        layout = layout_for(math.floor(108 * 980 / span))
        span = sum(width for _, width, _ in layout)
    left = (image.width - span) / 2
    for char, (glyph, width, offset) in zip(phrase, layout):
        draw.text((round(left + offset), 1536), char, font=glyph, anchor="ls",
                  fill=COLOR, stroke_width=1, stroke_fill="#14082e")
        left += width

