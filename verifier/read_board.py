"""read_board: the rows and cells it gives are the board's, cell for cell."""

from .boards import BOARDS
from .checks import board_problem, cells, result


def verify_input(value):
    problem = board_problem(value.board)
    if problem:
        return result(False, problem)
    return result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    """``output_value``: a contract BoardOutput, held to the board's true position."""
    number = input_value.board
    if output_value.board != number:
        return result(False, f"the output is for board {output_value.board}, not board {number}")
    true = list(BOARDS[number]["rows"])
    if output_value.size != len(true):
        return result(False, f"board {number} is {len(true)}x{len(true)}, not {output_value.size}x{output_value.size}")
    if list(output_value.rows) != true:
        return result(False, f"board {number}'s rows are not its position: {true}")
    for letter, given in (("X", output_value.x), ("O", output_value.o)):
        if list(given) != cells(true, letter):
            return result(False, f"board {number}'s {letter} cells are not its position: {cells(true, letter)}")
    return result(True, f"board {number}'s cells are its position")
