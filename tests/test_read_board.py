from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from contract import BoardInput
from plugin import read_board
from plugin.read_board import _rows, cell_box, cells, image_size, read_rows, templates
from verifier.boards import BOARDS

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("number", sorted(BOARDS))
def test_reads_each_boards_position_from_its_pixels(tmp_path: Path, number: int) -> None:
    rows = list(_rows(number))
    assert rows == list(BOARDS[number]["rows"])
    found = read_board(BoardInput(board=number), tmp_path)
    assert found.size == BOARDS[number]["size"] == len(rows)
    assert found.rows == rows and found.x == cells(rows, "X") and found.o == cells(rows, "O")
    assert len(found.x) + len(found.o) + len(BOARDS[number]["legal"]) == found.size**2


def test_names_cells_by_column_and_row_from_the_bottom() -> None:
    assert cells(["X..", ".O.", "..X"], "X") == ["a3", "c1"]
    assert cells(["X..", ".O.", "..X"], "O") == ["b2"]
    assert cells(["...X", "....", "....", "O..."], "X") == ["d4"]


def test_the_3_cell_templates_are_all_different() -> None:
    assert len(templates()) == 3


@pytest.mark.parametrize("number", [0, 51, -1])
def test_refuses_a_board_that_is_not_bundled(tmp_path: Path, number: int) -> None:
    with pytest.raises(ValueError, match="no board"):
        read_board(BoardInput(board=number), tmp_path)


def test_refuses_an_image_of_another_size() -> None:
    with pytest.raises(ValueError, match="344x344 or 444x444"):
        read_rows(Image.new("RGB", (400, 400)))


def test_refuses_a_cell_that_holds_something_else() -> None:
    with Image.open(ROOT / "ui" / "boards" / "board-01.png") as image:
        image = image.convert("RGB")
    left, top, _, _ = cell_box(3, 1, 2)  # b3
    image.putpixel((left + 3, top + 3), (255, 0, 0))
    with pytest.raises(ValueError, match="cell b3"):
        read_rows(image)


def test_both_grid_sizes_are_bundled() -> None:
    sizes = {Image.open(ROOT / "ui" / "boards" / f"board-{n:02d}.png").size[0] for n in BOARDS}
    assert sizes == {image_size(3), image_size(4)}


def test_nothing_the_agent_can_reach_holds_the_answers() -> None:
    for path in (ROOT / "src").rglob("*.py"):
        if path.name == "make_boards.py":
            continue  # the generator computes the answers; the plugin never runs it
        code = [line for line in path.read_text().splitlines() if not line.lstrip().startswith("#")]
        assert not any("verifier" in line for line in code if line.lstrip().startswith(("import ", "from "))), path
        assert not any("BOARDS" in line and "best" in line for line in code), path
