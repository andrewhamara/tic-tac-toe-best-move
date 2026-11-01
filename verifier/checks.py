"""Checks shared by the verifiers. Pure functions of contract instances and the boards' truth."""

import re

from .boards import COUNT

CELL = re.compile(r"^[a-d][1-4]$")


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def board_problem(number):
    if not 1 <= number <= COUNT:
        return f"no board {number}: the boards are 1 to {COUNT}"
    return None


def cells(rows, letter):
    """The cells holding ``letter``, by name, e.g. ['a1', 'b2']: as read_board lists them."""
    size = len(rows)
    return sorted("abcd"[column] + str(size - y) for y, line in enumerate(rows) for column, char in enumerate(line) if char == letter)
