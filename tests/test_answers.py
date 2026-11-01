"""The answers in verifier/boards.py, checked against a plain solver written apart from the generator."""

from __future__ import annotations

from collections import Counter

import pytest
from helpers import best, cell, free, mover, play, solve, won

from verifier.boards import BOARDS


@pytest.mark.parametrize("number", sorted(BOARDS))
def test_the_best_moves_are_an_independent_solvers(number: int) -> None:
    truth = BOARDS[number]
    rows = truth["rows"]
    assert list(truth["best"]) == best(rows)
    assert list(truth["legal"]) == sorted(cell(rows, y, x) for y, x in free(rows))
    result, plies = solve(rows)
    assert truth["outcome"] == ("draw" if result == 0 else f"win in {(plies + 1) // 2}")


@pytest.mark.parametrize("number", sorted(BOARDS))
def test_each_board_is_a_game_position_of_its_kind(number: int) -> None:
    truth = BOARDS[number]
    rows = truth["rows"]
    text = "".join(rows)
    assert text.count("X") - text.count("O") in (0, 1) and truth["to_move"] == mover(rows)
    assert not won(rows, "X") and not won(rows, "O") and free(rows)
    assert len(truth["best"]) < len(truth["legal"])  # some move is worse
    me, other = truth["to_move"], "O" if truth["to_move"] == "X" else "X"

    def threats(letter: str) -> list[str]:
        return [cell(rows, y, x) for y, x in free(rows) if won(play_as(rows, y, x, letter), letter)]

    kind = truth["kind"]
    if kind == "win-now":
        assert threats(me) and sorted(truth["best"]) == sorted(threats(me))
    elif kind == "block":
        assert not threats(me) and len(threats(other)) == 1 and list(truth["best"]) == threats(other)
    else:
        assert not threats(me) and not threats(other)
        assert truth["outcome"] == {"fork": "win in 2", "draw": "draw"}[kind]
    assert solve(rows)[0] >= 0  # never lost for the player to move


def play_as(rows: tuple[str, ...], y: int, x: int, letter: str) -> tuple[str, ...]:
    row = rows[y]
    return rows[:y] + (row[:x] + letter + row[x + 1 :],) + rows[y + 1 :]


def test_the_mix_of_boards() -> None:
    assert [BOARDS[n]["size"] for n in range(1, 51)] == [3] * 40 + [4] * 10
    assert Counter(BOARDS[n]["kind"] for n in range(1, 41)) == {"win-now": 10, "block": 10, "fork": 10, "draw": 10}
    assert Counter(BOARDS[n]["kind"] for n in range(41, 51)) == {"win-now": 3, "block": 3, "fork": 2, "draw": 2}


def test_no_two_boards_are_the_same_up_to_rotation_or_reflection() -> None:
    def turns(rows: tuple[str, ...]) -> set[tuple[str, ...]]:
        n, found = len(rows), set()
        for _ in range(4):
            rows = tuple("".join(rows[n - 1 - x][y] for x in range(n)) for y in range(n))
            found |= {rows, tuple(row[::-1] for row in rows)}
        return found

    forms = [min(turns(truth["rows"])) for truth in BOARDS.values()]
    assert len(set(forms)) == len(forms)


def test_a_winning_move_wins() -> None:
    for truth in BOARDS.values():
        if truth["kind"] == "win-now":
            rows = truth["rows"]
            y, x = len(rows) - int(truth["best"][0][1]), "abcd".index(truth["best"][0][0])
            assert won(play(rows, y, x), truth["to_move"])
