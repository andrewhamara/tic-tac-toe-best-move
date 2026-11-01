"""Shared test helpers: judging a submission as NanoAgent's sandbox would, and an independent solver."""

from __future__ import annotations

from functools import cache

from slimconfig import build_output

import verifier
from contract import TASKS, Task


def judge(board: int, player: str, move: str, changes: dict | None = None) -> dict:
    given, made = TASKS[Task.BEST_MOVE]
    answer = {"board": board, "player": player, "move": move} | (changes or {})
    return verifier.verify_task("best-move", build_output({"board": board}, given), build_output(answer, made), None, ".")


def checks(verdict: dict) -> dict:
    return {item["id"]: item["ok"] for item in verdict["details"]["constraints"]}


# A plain solver, written apart from the generator: a position is a tuple of rows, top row first.


def won(rows: tuple[str, ...], letter: str) -> bool:
    n = len(rows)
    lines = [[(y, x) for x in range(n)] for y in range(n)] + [[(y, x) for y in range(n)] for x in range(n)]
    lines += [[(i, i) for i in range(n)], [(i, n - 1 - i) for i in range(n)]]
    return any(all(rows[y][x] == letter for y, x in line) for line in lines)


def mover(rows: tuple[str, ...]) -> str:
    text = "".join(rows)
    return "X" if text.count("X") == text.count("O") else "O"


def cell(rows: tuple[str, ...], y: int, x: int) -> str:
    return "abcd"[x] + str(len(rows) - y)


def play(rows: tuple[str, ...], y: int, x: int) -> tuple[str, ...]:
    row = rows[y]
    return rows[:y] + (row[:x] + mover(rows) + row[x + 1 :],) + rows[y + 1 :]


def free(rows: tuple[str, ...]) -> list[tuple[int, int]]:
    return [(y, x) for y, row in enumerate(rows) for x, char in enumerate(row) if char == "."]


@cache
def solve(rows: tuple[str, ...]) -> tuple[int, int]:
    """(result, plies) for the player to move with best play: result 1 win, 0 draw, -1 loss; plies until
    the game ends. A win prefers fewer plies, a loss more."""
    options = [score(rows, y, x) for y, x in free(rows)]
    return max(options, key=rank) if options else (0, 0)


def score(rows: tuple[str, ...], y: int, x: int) -> tuple[int, int]:
    after = play(rows, y, x)
    if won(after, mover(rows)):
        return 1, 1
    result, plies = solve(after)
    return -result, plies + 1


def rank(option: tuple[int, int]) -> tuple[int, int]:
    result, plies = option
    return result, -plies if result > 0 else plies if result < 0 else 0


def best(rows: tuple[str, ...]) -> list[str]:
    top = rank(solve(rows))
    return sorted(cell(rows, y, x) for y, x in free(rows) if rank(score(rows, y, x)) == top)
