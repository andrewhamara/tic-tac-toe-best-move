"""read_board: the marks on a bundled tic-tac-toe board image, read cell by cell from its pixels.

A board is 3x3 or 4x4 cells of CELL px, LINE px apart, inside a MARGIN of coordinates; the image's
size says which. Every cell is empty or holds one of the two sprites in ui/marks.png, so each cell's
pixels equal exactly one of 3 templates. The board comes back as its rows and the cells each player
holds. A cell that matches none is refused: the boards hold nothing else. read_board says what stands
where and never which move is best: only the verifier holds the answers.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

from PIL import Image

from contract import BoardInput, BoardOutput

UI = Path(__file__).resolve().parents[2] / "ui"
BOARDS = UI / "boards"
MARKS = UI / "marks.png"  # 2 sprites of CELL px in a row, in the order of LETTERS
CELL = 96
LINE = 4
MARGIN = 24
PAPER = (255, 255, 255)
LETTERS = "XO"
COUNT = 50


def image_size(size: int) -> int:
    """The width and height in px of a board of ``size`` x ``size`` cells."""
    return 2 * MARGIN + size * CELL + (size - 1) * LINE


def board_path(number: int) -> Path:
    path = BOARDS / f"board-{number:02d}.png"
    if not 1 <= number <= COUNT or not path.is_file():
        raise ValueError(f"no board {number}: the boards are 1 to {COUNT}")
    return path


def cell_box(size: int, column: int, row: int) -> tuple[int, int, int, int]:
    """The box of the cell in ``column`` (0 = a) and ``row`` (0 = 1, the bottom row)."""
    left = MARGIN + column * (CELL + LINE)
    top = MARGIN + (size - 1 - row) * (CELL + LINE)
    return left, top, left + CELL, top + CELL


def cell_name(column: int, row: int) -> str:
    return "abcd"[column] + str(row + 1)


@cache
def sprites() -> tuple[Image.Image, ...]:
    with Image.open(MARKS) as sheet:
        sheet = sheet.convert("RGBA")
        return tuple(sheet.crop((i * CELL, 0, (i + 1) * CELL, CELL)) for i in range(len(LETTERS)))


def cell_image(letter: str) -> Image.Image:
    """A cell with the mark ``letter`` in it, or empty for '.'."""
    tile = Image.new("RGBA", (CELL, CELL), (*PAPER, 255))
    if letter != ".":
        tile.alpha_composite(sprites()[LETTERS.index(letter)])
    return tile.convert("RGB")


@cache
def templates() -> dict[bytes, str]:
    """Each cell's pixels -> what it holds: X, O or empty."""
    return {cell_image(letter).tobytes(): letter for letter in "." + LETTERS}


def read_rows(image: Image.Image) -> list[str]:
    """The board as its rows, the top row first, left to right: X, O or '.' per cell."""
    sizes = {image_size(size): size for size in (3, 4)}
    if image.size[0] != image.size[1] or image.size[0] not in sizes:
        raise ValueError(f"a board image is {' or '.join(f'{s}x{s}' for s in sizes)} px, not {image.size[0]}x{image.size[1]}")
    size = sizes[image.size[0]]
    image = image.convert("RGB")
    known = templates()
    rows = []
    for row in range(size - 1, -1, -1):
        line = ""
        for column in range(size):
            pixels = image.crop(cell_box(size, column, row)).tobytes()
            if pixels not in known:
                raise ValueError(f"cell {cell_name(column, row)} holds nothing a board holds")
            line += known[pixels]
        rows.append(line)
    return rows


@cache
def _rows(number: int) -> tuple[str, ...]:
    """The board's rows, read once: the bundled images never change."""
    with Image.open(board_path(number)) as image:
        return tuple(read_rows(image))


def cells(rows: list[str], letter: str) -> list[str]:
    """The cells holding ``letter``, by name, e.g. ['a1', 'b2']."""
    size = len(rows)
    return sorted(cell_name(column, size - 1 - y) for y, line in enumerate(rows) for column, char in enumerate(line) if char == letter)


def read_board(given: BoardInput, workspace: Path) -> BoardOutput:
    """What each cell of the board holds, read from its pixels: the rows and each player's cells."""
    rows = list(_rows(given.board))
    return BoardOutput(board=given.board, size=len(rows), rows=rows, x=cells(rows, "X"), o=cells(rows, "O"))
