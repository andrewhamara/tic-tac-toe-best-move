from __future__ import annotations

from pathlib import Path

import pytest
from helpers import checks, judge
from slimconfig import build_output, plain_output

import verifier
from contract import TASKS, TOOLS, BoardInput, Task, Tool
from plugin import read_board
from verifier.boards import BOARDS


def board_of(kind: str, size: int = 3) -> int:
    return next(n for n, b in sorted(BOARDS.items()) if b["kind"] == kind and b["size"] == size)


def legal_but_not_best(number: int) -> str:
    return next(m for m in BOARDS[number]["legal"] if m not in BOARDS[number]["best"])


def taken(number: int) -> str:
    size = BOARDS[number]["size"]
    return next(c + r for c in "abcd"[:size] for r in "1234"[:size] if c + r not in BOARDS[number]["legal"])


# Correct


@pytest.mark.parametrize("kind", ["win-now", "block", "fork", "draw"])
@pytest.mark.parametrize("size", [3, 4])
def test_approves_every_best_move(kind: str, size: int) -> None:
    n = board_of(kind, size)
    b = BOARDS[n]
    for move in b["best"]:
        verdict = judge(n, b["to_move"], move)
        assert verdict["valid"] is True and verdict["score"] == 1.0
        assert verdict["message"].startswith(f"All 6 checks hold: {move} is best on board {n}: ")


def test_the_message_says_what_the_best_move_forces() -> None:
    n = board_of("win-now")
    b = BOARDS[n]
    assert judge(n, b["to_move"], b["best"][0])["message"].endswith(f"{b['to_move']} wins at once.")
    n = board_of("fork")
    assert judge(n, BOARDS[n]["to_move"], BOARDS[n]["best"][0])["message"].endswith("wins in 2 moves.")
    n = board_of("draw")
    assert judge(n, BOARDS[n]["to_move"], BOARDS[n]["best"][0])["message"].endswith("holds the draw.")


# Incorrect


@pytest.mark.parametrize("kind", ["win-now", "block", "fork", "draw"])
def test_a_legal_move_that_is_not_best_scores_a_quarter(kind: str) -> None:
    n = board_of(kind)
    b = BOARDS[n]
    move = legal_but_not_best(n)
    verdict = judge(n, b["to_move"], move)
    assert verdict["valid"] is False and verdict["score"] == 0.25
    assert verdict["message"].startswith(f"best: {move} is legal but not best: with {' or '.join(b['best'])}, ")


def test_a_taken_cell_scores_zero() -> None:
    n = 1
    move = taken(n)
    verdict = judge(n, BOARDS[n]["to_move"], move)
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert verdict["message"] == f"legal: {move} is taken on board 1."
    assert checks(verdict)["best"] is None


def test_the_wrong_player_scores_zero() -> None:
    b = BOARDS[1]
    other = "O" if b["to_move"] == "X" else "X"
    verdict = judge(1, other, b["best"][0])
    assert verdict["valid"] is False and verdict["score"] == 0.0
    assert verdict["message"] == f"player: On board 1 it is {b['to_move']} to move, not {other}."


# Malformed and missing


@pytest.mark.parametrize("move", ["B2", "b 2", "2b", "e1", "a0", "", "b", "b22", "middle"])
def test_a_move_that_names_no_cell_scores_zero(move: str) -> None:
    verdict = judge(1, BOARDS[1]["to_move"], move)
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["message"].startswith("move-form:")


@pytest.mark.parametrize("move", ["d1", "a4", "d4"])
def test_a_4x4_cell_names_no_cell_of_a_3x3_board(move: str) -> None:
    verdict = judge(1, BOARDS[1]["to_move"], move)
    assert verdict["message"] == f"move-form: {move!r} is not a cell of a 3x3 board, a1 to c3."


def test_answering_another_board_scores_zero() -> None:
    b = BOARDS[1]
    verdict = judge(1, b["to_move"], b["best"][0], {"board": 2})
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["message"].startswith("same-question:")


@pytest.mark.parametrize("number", [0, 51])
def test_a_board_that_does_not_exist_scores_zero(number: int) -> None:
    verdict = judge(number, "X", "b2")
    assert verdict["valid"] is False and verdict["score"] == 0.0 and verdict["message"].startswith("board:")


# Boundary


def test_o_to_move_boards_are_judged_for_o() -> None:
    n = next(n for n, b in sorted(BOARDS.items()) if b["to_move"] == "O")
    assert judge(n, "O", BOARDS[n]["best"][0])["valid"] is True


def test_4x4_cells_are_cells_of_a_4x4_board() -> None:
    n = next(n for n, b in sorted(BOARDS.items()) if b["size"] == 4 and any(m[0] == "d" or m[1] == "4" for m in b["best"]))
    move = next(m for m in BOARDS[n]["best"] if m[0] == "d" or m[1] == "4")
    assert judge(n, BOARDS[n]["to_move"], move)["valid"] is True


def test_a_blocking_board_has_one_best_move() -> None:
    assert all(len(b["best"]) == 1 for b in BOARDS.values() if b["kind"] == "block")


# Tool calls


def test_checks_read_board_calls() -> None:
    def verify_input(number: int) -> bool:
        return verifier.verify_input("read_board", build_output({"board": number}, TOOLS[Tool.READ_BOARD][0]))["valid"]

    assert verify_input(1) and verify_input(50) and not verify_input(0) and not verify_input(51)

    def verify_output(number: int, made: dict) -> dict:
        given, output = TOOLS[Tool.READ_BOARD]
        return verifier.verify_output("read_board", build_output({"board": number}, given), build_output(made, output), ".")

    found = plain_output(read_board(BoardInput(board=1), Path(".")))
    assert verify_output(1, found)["valid"] is True
    assert "board 1's X cells are not its position" in verify_output(1, found | {"x": found["x"][:-1]})["message"]
    assert "board 1's rows are not its position" in verify_output(1, found | {"rows": found["rows"][::-1]})["message"]
    assert "is 3x3, not 4x4" in verify_output(1, found | {"size": 4})["message"]
    assert verify_output(2, found)["valid"] is False


def test_the_show_board_task_is_judged_as_its_tool() -> None:
    found = plain_output(read_board(BoardInput(board=45), Path(".")))
    given, made = TASKS[Task.SHOW_BOARD]
    verdict = verifier.verify_task("show-board", build_output({"board": 45}, given), build_output(found, made), None, ".")
    assert verdict["valid"] is True


def test_the_verdict_is_the_same_twice() -> None:
    assert judge(3, "X", "a1") == judge(3, "X", "a1")
