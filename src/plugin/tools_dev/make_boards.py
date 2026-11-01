"""Builds the bundled boards: ui/marks.png (once), ui/boards/board-NN.png, and verifier/boards.py.

    uv run python -m plugin.tools_dev.make_boards

Every board is a position reachable in a real game: X moves first, the players alternate, and nobody
has won yet. Boards 1 to 40 are 3x3, three in a row wins: from every such position, one per
rotation or reflection, a seeded shuffle picks 10 of each kind below, each drawn turned or flipped at
random. Boards 41 to 50 are 4x4, four
in a row wins: seeded random games stopped after 6 to 10 marks give 3 win-now, 3 block, 2 fork and 2
draw boards. The kinds, for the player to move:

- win-now: it can complete a line with this move;
- block: it cannot, and the opponent threatens exactly one line, which it must block;
- fork: neither threatens a line, and it can force a win on its next move (two threats at once);
- draw: neither threatens a line, and the best it can force is a draw.

Every board has a move that is not best, and none is lost for the player to move. The answers are
computed exactly by searching the whole game: a move's value is a win (sooner is better), a draw, or a
loss (later is better), and the best moves are every move of the best value. Running it again writes
the same files.
"""

from __future__ import annotations

import random
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from plugin.read_board import (
    BOARDS,
    CELL,
    COUNT,
    LETTERS,
    LINE,
    MARGIN,
    MARKS,
    PAPER,
    cell_box,
    cell_image,
    cell_name,
    image_size,
    read_rows,
)

ROOT = Path(__file__).resolve().parents[3]
TRUTH = ROOT / "verifier" / "boards.py"
SEED = 580
KINDS = ("win-now", "block", "fork", "draw")
SMALL = {kind: 10 for kind in KINDS}  # boards 1 to 40, 3x3
LARGE = {"win-now": 3, "block": 3, "fork": 2, "draw": 2}  # boards 41 to 50, 4x4
X_COLOR = (28, 78, 160)
O_COLOR = (201, 42, 42)
GRID = (60, 60, 60)


def make_marks() -> None:
    """ui/marks.png: the X and O sprites, drawn 4 times larger and scaled down for smooth edges."""
    big = 4 * CELL
    sheet = Image.new("RGBA", (big * len(LETTERS), big), (0, 0, 0, 0))
    pen = ImageDraw.Draw(sheet)
    inset, width = 4 * 22, 4 * 10
    pen.line((inset, inset, big - inset, big - inset), fill=X_COLOR, width=width)
    pen.line((inset, big - inset, big - inset, inset), fill=X_COLOR, width=width)
    pen.ellipse((big + inset, inset, 2 * big - inset, big - inset), outline=O_COLOR, width=width)
    sheet.resize((CELL * len(LETTERS), CELL), Image.Resampling.LANCZOS).save(MARKS)


# A board is a string of size * size characters, the top row first: X, O or '.'.


@cache
def lines(size: int) -> tuple[tuple[int, ...], ...]:
    """Every winning line: each row, each column and both diagonals, size cells long."""
    rows = [tuple(y * size + x for x in range(size)) for y in range(size)]
    columns = [tuple(y * size + x for y in range(size)) for x in range(size)]
    diagonals = [tuple(i * size + i for i in range(size)), tuple(i * size + size - 1 - i for i in range(size))]
    return tuple(rows + columns + diagonals)


def size_of(board: str) -> int:
    return {9: 3, 16: 4}[len(board)]


def winner(board: str) -> str | None:
    for line in lines(size_of(board)):
        first = board[line[0]]
        if first != "." and all(board[i] == first for i in line):
            return first
    return None


def to_move(board: str) -> str:
    return "X" if board.count("X") == board.count("O") else "O"


def place(board: str, cell: int, letter: str) -> str:
    return board[:cell] + letter + board[cell + 1 :]


def empties(board: str) -> list[int]:
    return [i for i, char in enumerate(board) if char == "."]


@cache
def value(board: str) -> int:
    """The position's value for the player to move: a win is the empty cells left when it is made (so
    sooner is more), a loss the negative of the opponent's, a draw 0."""
    letter = to_move(board)
    best = None
    for cell in empties(board):
        after = place(board, cell, letter)
        score = len(empties(board)) if winner(after) else -value(after) if empties(after) else 0
        best = score if best is None else max(best, score)
    return 0 if best is None else best


def move_value(board: str, cell: int) -> int:
    after = place(board, cell, to_move(board))
    return len(empties(board)) if winner(after) else -value(after) if empties(after) else 0


def name(board: str, cell: int) -> str:
    size = size_of(board)
    return cell_name(cell % size, size - 1 - cell // size)


def best_moves(board: str) -> list[str]:
    top = value(board)
    return sorted(name(board, cell) for cell in empties(board) if move_value(board, cell) == top)


def outcome(board: str) -> str:
    """The best result the player to move can force: 'win in N' (its own moves), 'draw' or 'loss in N'."""
    top = value(board)
    if top == 0:
        return "draw"
    moves = (len(empties(board)) - abs(top)) // 2 + 1
    return f"{'win' if top > 0 else 'loss'} in {moves}"


def threats(board: str, letter: str) -> list[int]:
    """The empty cells where ``letter`` would complete a line."""
    return [cell for cell in empties(board) if winner(place(board, cell, letter))]


def kind(board: str) -> str | None:
    """The board's kind (see the module docstring), or None when it is none of them."""
    letter = to_move(board)
    other = "O" if letter == "X" else "X"
    if value(board) < 0 or len(best_moves(board)) == len(empties(board)):
        return None  # lost, or no move is worse than another
    if threats(board, letter):
        return "win-now"
    if threats(board, other):
        return "block" if len(threats(board, other)) == 1 else None
    if outcome(board) == "win in 2":
        return "fork"
    if outcome(board) == "draw":
        return "draw"
    return None


def symmetries(board: str) -> list[str]:
    """The board's 8 rotations and reflections."""
    size = size_of(board)
    grid = [board[y * size : (y + 1) * size] for y in range(size)]
    found = []
    for _ in range(4):
        grid = ["".join(grid[size - 1 - x][y] for x in range(size)) for y in range(size)]  # a quarter turn
        found += ["".join(grid), "".join(row[::-1] for row in grid)]
    return found


def canonical(board: str) -> str:
    return min(symmetries(board))


def all_small() -> list[str]:
    """Every 3x3 position reachable in a game and not yet won or full, one per rotation or reflection."""
    seen = set()
    stack = ["." * 9]
    while stack:
        board = stack.pop()
        if canonical(board) in seen:
            continue
        seen.add(canonical(board))
        if winner(board) or not empties(board):
            continue
        stack += [place(board, cell, to_move(board)) for cell in empties(board)]
    return sorted(board for board in seen if not winner(board) and empties(board))


def pick(candidates, quota: dict[str, int]) -> list[str]:
    chosen, left = [], dict(quota)
    for board in candidates:
        found = kind(board)
        if found and left.get(found, 0) > 0 and canonical(board) not in {canonical(b) for b in chosen}:
            chosen.append(board)
            left[found] -= 1
        if not any(left.values()):
            return chosen
    raise SystemExit(f"not enough boards: still need {left}")


def large_games(rng: random.Random):
    """4x4 positions from random games, stopped after 6 to 10 marks before anybody wins."""
    while True:
        board, marks = "." * 16, rng.randint(6, 10)
        for _ in range(marks):
            board = place(board, rng.choice(empties(board)), to_move(board))
            if winner(board):
                break
        if not winner(board):
            yield board


def draw(board: str) -> Image.Image:
    size = size_of(board)
    side = image_size(size)
    image = Image.new("RGB", (side, side), PAPER)
    pen = ImageDraw.Draw(image)
    for i in range(1, size):
        at = MARGIN + i * (CELL + LINE) - LINE
        pen.rectangle((at, MARGIN, at + LINE - 1, side - MARGIN - 1), fill=GRID)
        pen.rectangle((MARGIN, at, side - MARGIN - 1, at + LINE - 1), fill=GRID)
    for cell, letter in enumerate(board):
        column, row = cell % size, size - 1 - cell // size
        image.paste(cell_image(letter), cell_box(size, column, row)[:2])
    font = ImageFont.load_default(size=14)
    for i in range(size):
        middle = MARGIN + i * (CELL + LINE) + CELL // 2
        pen.text((middle, side - MARGIN // 2), "abcd"[i], font=font, fill=(90, 90, 90), anchor="mm")
        pen.text((MARGIN // 2, middle), str(size - i), font=font, fill=(90, 90, 90), anchor="mm")
    return image


def main() -> None:
    if not MARKS.is_file():
        make_marks()
    rng = random.Random(SEED)
    small = all_small()
    rng.shuffle(small)
    chosen = [rng.choice(symmetries(board)) for board in pick(small, SMALL)]  # each turned or flipped at random
    large = pick(large_games(rng), LARGE)
    rng.shuffle(chosen)
    rng.shuffle(large)
    boards = chosen + large
    if len(boards) != COUNT:
        raise SystemExit(f"{len(boards)} boards, not {COUNT}")
    BOARDS.mkdir(parents=True, exist_ok=True)
    lines_out = [
        '"""Each bundled board\'s position and answers, as src/plugin/tools_dev/make_boards.py computed them by',
        "searching the whole game. Generated: do not edit.",
        "",
        "rows: the board as read_board gives it; to_move: X or O; kind: win-now, block, fork or draw;",
        "outcome: the best result the player to move can force; best: every move that forces it soonest (a",
        'win) or latest (a loss); legal: every empty cell."""',
        "",
        f"COUNT = {COUNT}",
        "BOARDS = {",
    ]
    for number, board in enumerate(boards, 1):
        size = size_of(board)
        rows = [board[y * size : (y + 1) * size] for y in range(size)]
        path = BOARDS / f"board-{number:02d}.png"
        draw(board).save(path, optimize=True)
        with Image.open(path) as saved:
            if read_rows(saved) != rows:
                raise SystemExit(f"{path}: read_board does not read back the board drawn")
        legal = sorted(name(board, cell) for cell in empties(board))
        lines_out.append(
            f"    {number}: {{'size': {size}, 'rows': {tuple(rows)!r}, 'to_move': {to_move(board)!r}, "
            f"'kind': {kind(board)!r}, 'outcome': {outcome(board)!r}, 'best': {tuple(best_moves(board))!r}, "
            f"'legal': {tuple(legal)!r}}},"
        )
    lines_out.append("}")
    TRUTH.write_text("\n".join(lines_out) + "\n")
    print(f"wrote {COUNT} boards to {BOARDS} and their answers to {TRUTH}")


if __name__ == "__main__":
    main()
