# Tic-Tac-Toe Best Move

A `nanoagent.plugin/v0001` plugin: find the best move on a tic-tac-toe board image.
Each of 50 bundled boards is a position from a real game, nobody has won yet, and whose turn it
is shows on the board: X moves first. Its one tool reads the board's pixels and returns the
board as text; the agent must find the move itself. The verifier holds every best move, found
by searching the whole game, and checks the agent's move against them.

## Tools

| Tool | Does | Code |
|---|---|---|
| `read_board` | Reads a board image cell by cell, each cell matched exactly against the 3 a cell can hold (X, O, empty), and gives the rows and the cells X and O hold, e.g. `a1, b2`. It never says which move is best | `src/plugin/read_board.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `best-move` | Finds the best move on a board for the player to move, e.g. "find the best move on board 7" | `agent`, with `read_board`; no reference (the verifier holds the answers) |
| `show-board` | Shows a board and what the agent reads | `tool` (`read_board`) |

The page draws each answer on the board (`ui/renderers.js`): the agent's cell
framed in orange and, when it is wrong, each best cell framed in dashed green,
under a line naming both, with the verdict's checks folded away.

## The task

The input is a board, 1 to 50. **Boards 1 to 40 are 3x3, three in a row wins;
boards 41 to 50 are 4x4, four in a row (a whole row, column or diagonal)
wins.** The agent submits the player to move and the cell to mark, a column
letter from the left and a row number from the bottom, e.g. `b2`. The best
move is defined exactly: a move that forces the best result for the player to
move, the soonest win, else a draw.

Each board is one of four kinds, for the player to move:

| Kind | Boards (3x3 + 4x4) | The position |
|---|---|---|
| win-now | 10 + 3 | It can complete a line with this move |
| block | 10 + 3 | It cannot, and the opponent threatens exactly one line, which it must block |
| fork | 10 + 2 | Neither threatens a line, and it can force a win on its next move: two threats at once |
| draw | 10 + 2 | Neither threatens a line, and the best it can force is a draw, though some moves lose |

## Ground truth

`src/plugin/tools_dev/make_boards.py` builds the boards with a fixed seed. The
3x3 boards come from every position reachable in a game, one per rotation or
reflection: a shuffle picks 10 of each kind, and each is drawn turned or
flipped at random. The 4x4 boards come from random games stopped after 6 to
10 marks. For each board the generator searches the whole rest of the game,
writes every best move to `verifier/boards.py`, and refuses to write a board
unless `read_board` reads it back. The tests check every answer against a
second solver written apart from the generator, and every board's kind. Every
board has a move that is not best, and none is lost for the player to move.
The plugin's tool holds no answers; the verifier, standard library only,
judges from them.

## Constraints

`verifier/task.py` judges a `best-move` submission against 6 constraints, in
order. Each entry of `details.constraints` is
`{id, constraint, ok, expected, actual, message}`.

| # | id | What it checks |
|---|---|---|
| 1 | `board` | The board exists |
| 2 | `same-question` | The submission answers the question asked: its board |
| 3 | `player` | The player given is the one to move on this board |
| 4 | `move-form` | The move names a cell of this board, e.g. `b2` (`d4` only on a 4x4 board) |
| 5 | `legal` | The cell is empty |
| 6 | `best` | The move forces the best result: the soonest win, else a draw |

A best move scores 1. A legal move that is not best scores 0.25. Anything
else, a taken cell or a failure of 1 to 4, scores 0. Every tool output is
checked too: `read_board`'s rows and cells must be the board's.

## Limitations

- **Small on purpose.** RUSH Lab's model must answer within 2,048-token replies, thinking included, and ran out of them on chess positions (see Chess Best Move). Tic-tac-toe is small enough to work through; the 4x4 boards are the harder set.
- **"Best" counts only the result.** Among moves that keep a draw, all are equally best, even when one sets more traps.
- **The agent never sees pixels.** It reasons over the board as text; the board reader does the seeing, on these rendered boards only.
- **A fixed set of 50 boards** could in principle be memorized.

## Layout

```text
.
├── nanoagent.yaml   # manifest: id, runtime, permissions (no network), tools, tasks and the agent's instructions
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml   # pillow reads the boards
├── uv.lock
├── .gitignore
├── .env             # needed environment variable names (none here)
├── src/plugin/      # the MCP server (__main__.py), read_board.py, and tools_dev/make_boards.py
├── tests/           # the reader, the answers against a second solver, the verifier, scripted agents
├── ui/              # boards/ (the 50 PNGs), marks.png (the X and O sprites), renderers.js/.css (moves on the board)
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier: boards.py (the answers), one module per tool, and task.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run python -m plugin.tools_dev.make_boards   # rewrites the same boards and answers
```

NanoAgent passes the folder the plugin may write to as `NANOAGENT_WORKSPACE`;
this plugin writes nothing there.
