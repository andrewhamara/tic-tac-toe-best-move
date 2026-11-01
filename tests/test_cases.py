"""Scripted agents, no model, each run as NanoAgent runs the task: read_board, then submit.

An exact agent, which knows the answers, must pass every board. A simple agent sees only what the
model sees, read_board's rows: it wins now if it can, else blocks, else takes the first empty cell. Its
verdicts must agree with whether that move is best.
"""

from __future__ import annotations

from pathlib import Path

from helpers import cell, free, judge, mover, won

from contract import BoardInput
from plugin import read_board
from verifier.boards import BOARDS


def simple_move(number: int) -> tuple[str, str]:
    rows = tuple(read_board(BoardInput(board=number), Path(".")).rows)
    me = mover(rows)
    other = "O" if me == "X" else "X"
    for letter in (me, other):
        for y, x in free(rows):
            row = rows[y]
            if won(rows[:y] + (row[:x] + letter + row[x + 1 :],) + rows[y + 1 :], letter):
                return me, cell(rows, y, x)
    y, x = free(rows)[0]
    return me, cell(rows, y, x)


def test_an_exact_agent_passes_every_board() -> None:
    for number, truth in BOARDS.items():
        assert judge(number, truth["to_move"], truth["best"][0])["valid"] is True


def test_a_simple_agent_is_judged_by_its_move() -> None:
    found = {kind: 0 for kind in ("win-now", "block", "fork", "draw")}
    for number, truth in BOARDS.items():
        player, move = simple_move(number)
        verdict = judge(number, player, move)
        assert verdict["valid"] is (move in truth["best"])
        assert verdict["score"] == (1.0 if move in truth["best"] else 0.25)
        found[truth["kind"]] += move in truth["best"]
    # Winning now and blocking find every win-now and block board; the rest need lookahead.
    assert found["win-now"] == 13 and found["block"] == 13
    print(f"win, else block, else the first empty cell is best on {sum(found.values())} of {len(BOARDS)}: {found}")
