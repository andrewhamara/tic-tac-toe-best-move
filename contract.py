"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    READ_BOARD = "read_board"


class Task(Enum):
    BEST_MOVE = "best-move"
    SHOW_BOARD = "show-board"


class Mark(Enum):
    X = "X"
    O = "O"


BOARD = "A bundled board image's number, 1 to 50: boards 1 to 40 are 3x3, 41 to 50 are 4x4"
MOVE = (
    "The cell to mark: its column letter, then its row number, e.g. b2; columns a, b, c (and d on a 4x4 board) "
    "from the left, rows 1, 2, 3 (and 4) from the bottom"
)


@dataclass
class BoardInput(Output):
    board: Annotated[int, BOARD]


@dataclass
class BoardOutput(Output):
    board: Annotated[int, BOARD]
    size: Annotated[int, "The grid's width: 3 (three in a row wins) or 4 (four in a row wins)"]
    rows: Annotated[list[str], "The grid row by row, the top row first, left to right: X, O, or . for an empty cell"]
    x: Annotated[list[str], "The cells X holds, e.g. a1, b2: column letter from the left, row number from the bottom"]
    o: Annotated[list[str], "The cells O holds, written the same way"]


@dataclass
class MoveInput(Output):
    board: Annotated[int, BOARD]


@dataclass
class MoveOutput(Output):
    board: Annotated[int, "The board's number, as given"]
    player: Annotated[Mark, "The player to move: X moves first, so X when both have as many marks, else O"]
    move: Annotated[str, MOVE]


TOOLS = {
    Tool.READ_BOARD: (BoardInput, BoardOutput),
}
TASKS = {
    Task.BEST_MOVE: (MoveInput, MoveOutput),
    Task.SHOW_BOARD: (BoardInput, BoardOutput),
}
