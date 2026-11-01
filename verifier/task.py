"""The best-move task's verdict: the agent's move against every best move, found by searching the whole game.

Six constraints, in order; every one must hold. Each is {id, constraint, ok, expected, actual,
message}: ok is true, false, or null when a constraint it needs did not hold. Any failure of 1 to 4
scores 0, and so does a cell that is taken. A legal move that is not a best move scores 0.25; a best
move scores 1.
"""

from .boards import BOARDS
from .checks import CELL, board_problem, result

CONSTRAINTS = (
    ("board", "The board exists"),
    ("same-question", "The submission answers the question asked: its board"),
    ("player", "The player given is the one to move on this board"),
    ("move-form", "The move names a cell of this board, e.g. b2"),
    ("legal", "The cell is empty"),
    ("best", "The move forces the best result: the soonest win, else a draw"),
)
GUARDS = 4  # constraints 1 to 4: a failure scores 0
LEGAL = 0.25  # a legal move that is not a best move


def outcome_text(player, outcome):
    if outcome == "draw":
        return f"{player} holds the draw"
    moves = int(outcome.split()[-1])
    return f"{player} wins at once" if moves == 1 else f"{player} wins in {moves} moves"


def verify_task(arguments, output, reference, workspace):
    """``arguments``: a contract MoveInput; ``output``: MoveOutput. No reference: the verifier holds the answers."""
    checks = {}

    def put(key, ok, expected=None, actual=None, message=""):
        checks[key] = {"ok": ok, "expected": expected, "actual": actual, "message": "" if ok else message}

    number = arguments.board
    problem = board_problem(number)
    put("board", problem is None, message=problem)
    truth = BOARDS[number] if problem is None else None
    put(
        "same-question",
        output.board == number,
        number,
        output.board,
        f"The question was board {number}; the submission answers board {output.board}.",
    )
    player = output.player.value
    if truth is not None:
        put(
            "player",
            player == truth["to_move"],
            truth["to_move"],
            player,
            f"On board {number} it is {truth['to_move']} to move, not {player}.",
        )
    move = output.move
    size = truth["size"] if truth is not None else 4
    on_board = bool(CELL.fullmatch(move)) and "abcd".index(move[0]) < size and int(move[1]) <= size
    last = "abcd"[size - 1] + str(size)
    put("move-form", on_board, actual=move, message=f"{move!r} is not a cell of a {size}x{size} board, a1 to {last}.")
    if truth is not None and on_board:
        best = list(truth["best"])
        put("legal", move in truth["legal"], actual=move, message=f"{move} is taken on board {number}.")
        if checks["legal"]["ok"]:
            put(
                "best",
                move in best,
                best,
                move,
                f"{move} is legal but not best: with {' or '.join(best)}, "
                f"{outcome_text(truth['to_move'], truth['outcome'])}.",
            )

    constraints = []
    for key, text in CONSTRAINTS:
        check = checks.get(key)
        if check is None:
            waiting = next(k for k, _ in CONSTRAINTS if checks.get(k, {"ok": True})["ok"] is False)
            check = {"ok": None, "expected": None, "actual": None, "message": f"Not checked: {waiting} did not hold."}
        constraints.append({"id": key, "constraint": text, **check})
    failed = [item for item in constraints if item["ok"] is False]
    details = {"constraints": constraints}
    if truth is not None:
        details |= {"expected": {"best": list(truth["best"]), "outcome": truth["outcome"], "kind": truth["kind"]}}
    if not failed:
        return result(
            True,
            f"All {len(CONSTRAINTS)} checks hold: {move} is best on board {number}: "
            f"{outcome_text(player, truth['outcome'])}.",
            **details,
        )
    first = failed[0]
    message = f"{first['id']}: {first['message']}" + (f" (+{len(failed) - 1} more)" if len(failed) > 1 else "")
    ok = {item["id"]: item["ok"] for item in constraints}
    score = LEGAL if all(ok[key] for key, _ in CONSTRAINTS[:GUARDS]) and ok.get("legal") else 0.0
    return result(False, message, score=score, **details)
