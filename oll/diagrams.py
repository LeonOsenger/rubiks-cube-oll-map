"""Render OLL case orientations as SVG diagrams.

State encoding (see ``CaseOrientation.state``):
    edges   UB UR UF UL    0 = oriented, 1 = flipped (yellow faces that edge's side)
    corners UBL UBR UFR UFL 0 = oriented, 1/2 = yellow faces the first/second side
            listed in ``CORNER_SIDES`` (clockwise order around the corner).
"""

from django.core.files.base import ContentFile
from django.utils.html import escape

YELLOW = "#FFD500"
GREY = "#7F7F7F"
OUTLINE = "#1A1A1A"

# Front-face colour for each rotation, in clockwise U order (F -> R -> B -> L).
SIDE_COLORS = [
    ("red", "#C41E3A"),
    ("green", "#009E60"),
    ("orange", "#FF5800"),
    ("blue", "#0051BA"),
]
FACES = ("F", "R", "B", "L")

EDGES = ("UB", "UR", "UF", "UL")
CORNERS = ("UBL", "UBR", "UFR", "UFL")
EDGE_SIDE = {
    "UB": "B",
    "UR": "R",
    "UF": "F",
    "UL": "L"
}
CORNER_SIDES = {
    "UBL": ("L", "B"),
    "UBR": ("B", "R"),
    "UFR": ("R", "F"),
    "UFL": ("F", "L")
}

# (row, col) on the top grid; row 0 is the back.
TOP_POSITION = {
    "UBL": (0, 0),
    "UB": (0, 1),
    "UBR": (0, 2),
    "UL": (1, 0),
    "UR": (1, 2),
    "UFL": (2, 0),
    "UF": (2, 1),
    "UFR": (2, 2),
}

# Pieces along each side strip, in drawing order (left→right for B/F, top→bottom for L/R).
SIDE_PIECES = {
    "B": ("UBL", "UB", "UBR"),
    "R": ("UBR", "UR", "UFR"),
    "F": ("UFL", "UF", "UFR"),
    "L": ("UBL", "UL", "UFL"),
}

CELL = 30
STRIP = 10
GAP = 3
PAD = 1.5
GRID_START = STRIP + GAP
SIZE = 2 * GRID_START + 3 * CELL


def face_colors(rotation):
    """Map each side face (F/R/B/L) to its (name, hex) colour for a rotation (0–3)."""
    return {
        face: SIDE_COLORS[(rotation + i) % 4] for i, face in enumerate(FACES)
    }


def front_color_name(rotation):
    return SIDE_COLORS[rotation % 4][0]


def sticker_colors(state, rotation):
    """Return ``(top, sides)`` hex colours for a state string and rotation.

    ``top`` is a 3×3 list of rows (back row first). ``sides`` maps each face to its three
    stickers in ``SIDE_PIECES`` order.
    """
    edge_digits, corner_digits = state[:4], state[4:]
    faces = face_colors(rotation)

    yellow_side = {}  # piece -> face its yellow sticker points to (absent = up)
    for edge, digit in zip(EDGES, edge_digits, strict=True):
        if digit == "1":
            yellow_side[edge] = EDGE_SIDE[edge]

    for corner, digit in zip(CORNERS, corner_digits, strict=True):
        if digit in "12":
            yellow_side[corner] = CORNER_SIDES[corner][int(digit) - 1]

    top = [[YELLOW] * 3 for _ in range(3)]
    for piece, (row, col) in TOP_POSITION.items():
        if piece in yellow_side:
            top[row][col] = GREY

    sides = {
        face: [YELLOW if yellow_side.get(piece) == face else faces[face][1] for piece in pieces]
        for face, pieces in SIDE_PIECES.items()
    }

    return top, sides


def _rect(x, y, w, h, fill):
    return (
        f'<rect x="{x + PAD:g}" y="{y + PAD:g}" width="{w - 2 * PAD:g}" '
        f'height="{h - 2 * PAD:g}" rx="2" fill="{fill}"/>'
    )


def render_svg(state, rotation, title=""):
    """Render a state/rotation as a standalone SVG document string."""
    top, sides = sticker_colors(state, rotation)
    far = GRID_START + 3 * CELL + GAP  # start of the right/bottom strips

    parts = []
    for row in range(3):
        for col in range(3):
            parts.append(
                _rect(GRID_START + col * CELL, GRID_START + row * CELL, CELL, CELL, top[row][col])
            )

    for i in range(3):
        offset = GRID_START + i * CELL
        parts.append(_rect(offset, 0, CELL, STRIP, sides["B"][i]))
        parts.append(_rect(offset, far, CELL, STRIP, sides["F"][i]))
        parts.append(_rect(0, offset, STRIP, CELL, sides["L"][i]))
        parts.append(_rect(far, offset, STRIP, CELL, sides["R"][i]))

    title_tag = f"<title>{escape(title)}</title>" if title else ""
    body = "".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
        f'width="{SIZE * 2}" height="{SIZE * 2}">{title_tag}'
        f'<rect x="{GRID_START - GAP / 2:g}" y="{GRID_START - GAP / 2:g}" '
        f'width="{3 * CELL + GAP:g}" height="{3 * CELL + GAP:g}" rx="3" fill="{OUTLINE}"/>'
        f"{body}</svg>\n"
    )


def diagram_filename(orientation):
    """Human-readable file name, e.g. ``oll-27_rot090_green-front.svg``."""
    degrees = orientation.rotation * 90
    color = front_color_name(orientation.rotation)
    return f"oll-{orientation.case.number:02d}_rot{degrees:03d}_{color}-front.svg"


def generate_diagram(orientation):
    """Render the orientation's SVG and store it on ``orientation.diagram``, replacing any
    previous file so the name stays stable."""
    field = orientation.diagram
    name = diagram_filename(orientation)
    target = field.field.generate_filename(orientation, name)

    if field:
        field.delete(save=False)

    if field.storage.exists(target):
        field.storage.delete(target)

    title = f"{orientation.case} – {orientation.get_rotation_display()}, " + (
        f"{front_color_name(orientation.rotation)} front"
    )
    svg = render_svg(orientation.state, orientation.rotation, title=title)
    field.save(name, ContentFile(svg.encode()), save=False)
    orientation.save(update_fields=["diagram"])

    return field.name
