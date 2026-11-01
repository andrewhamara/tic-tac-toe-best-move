// How this plugin's page draws its outputs: the board image (ui/boards/) with an SVG drawn over it as
// a data: image. A best-move answer leads with the agent's move and the best ones, frames the agent's
// cell in orange and, when it is wrong, each best cell in dashed green, with the verdict's checks
// folded away. show-board shows a board and what the agent reads.
import { disclosure, h } from "./kit/components.js";

const CELL = 96;
const LINE = 4;
const MARGIN = 24;
const AGENT = "#f08c00";
const BEST = "#2b8a3e";
const side = (size) => 2 * MARGIN + size * CELL + (size - 1) * LINE;
const file = (n) => `boards/board-${String(n).padStart(2, "0")}.png`;
// Boards 1 to 40 are 3x3 and 41 to 50 are 4x4.
const sizeOf = (board) => (board > 40 ? 4 : 3);

/** A frame around a cell, e.g. "b2", or nothing when the move names no cell of the board. */
function frame(size, move, color, dashed) {
  if (!/^[a-d][1-4]$/.test(move)) return "";
  const col = "abcd".indexOf(move[0]);
  const row = Number(move[1]) - 1;
  if (col >= size || row >= size) return "";
  const x = MARGIN + col * (CELL + LINE) + 6;
  const y = MARGIN + (size - 1 - row) * (CELL + LINE) + 6;
  const dash = dashed ? ' stroke-dasharray="12 8"' : "";
  return `<rect x="${x}" y="${y}" width="${CELL - 12}" height="${CELL - 12}" rx="8" fill="none" stroke="${color}" stroke-width="7"${dash}/>`;
}

const svg = (size, parts) =>
  `data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${side(size)} ${side(size)}">${parts.join("")}</svg>`)}`;

const picture = (board, overlay) =>
  h(
    "div",
    { class: "ttt-frame" },
    h("img", { class: "ttt-img", src: file(board), alt: `Board ${board}`, width: side(sizeOf(board)), height: side(sizeOf(board)) }),
    overlay ? h("img", { class: "ttt-overlay", src: svg(sizeOf(board), overlay), alt: "" }) : null,
  );

const MARKS = { true: ["✓", "ok"], false: ["✗", "bad"], null: ["·", "skipped"] };

/** The verdict's checks, each with its mark and, when it failed or was skipped, why. */
const checks = (constraints) =>
  h(
    "ol",
    { class: "ttt-checks" },
    constraints.map(({ id, constraint, ok, message }) => {
      const [mark, tone] = MARKS[String(ok)];
      return h(
        "li",
        { class: `ttt-check ${tone}` },
        h("span", { class: "ttt-mark", text: mark }),
        h("span", {}, h("code", { text: id }), ` ${constraint}`, message ? h("span", { class: "ttt-why", text: message }) : null),
      );
    }),
  );

const OUTCOMES = { draw: "a draw at best", "win in 1": "wins now", "win in 2": "wins next move" };

export default {
  BoardOutput: ({ board, rows, x, o }) =>
    h(
      "div",
      { class: "ttt-card" },
      picture(board, null),
      disclosure(
        { summary: "What the agent reads", className: "ttt-text" },
        h("p", { class: "ttt-cells", text: rows.join(" / ") }),
        h("p", { class: "ttt-cells" }, h("strong", { text: "X: " }), x.join(", ") || "none"),
        h("p", { class: "ttt-cells" }, h("strong", { text: "O: " }), o.join(", ") || "none"),
      ),
    ),
  MoveOutput: ({ board, player, move }, { verdict }) => {
    const details = verdict.details || {};
    const expected = details.expected || {};
    const best = expected.best || [];
    const right = best.includes(move);
    const size = sizeOf(board);
    const overlay = [frame(size, move, AGENT, false)];
    if (best.length && !right) best.forEach((cell) => overlay.push(frame(size, cell, BEST, true)));
    const result = OUTCOMES[expected.outcome] || expected.outcome;
    return h(
      "div",
      { class: "ttt-card" },
      h(
        "p",
        { class: "ttt-move" },
        h("span", { class: "muted", text: `${player}'s move ` }),
        h("strong", { text: move }),
        best.length ? h("span", { class: `ttt-verdict ${right ? "ok" : "bad"}`, text: right ? " ✓" : " ✗" }) : null,
        best.length ? h("span", { class: "muted", text: ` · best ${best.join(" or ")} (${result})` }) : null,
      ),
      picture(board, overlay),
      h(
        "p",
        { class: "ttt-legend muted" },
        h("span", { class: "ttt-key" }, h("span", { class: "ttt-swatch agent" }), "the agent's move"),
        best.length && !right ? h("span", { class: "ttt-key" }, h("span", { class: "ttt-swatch best" }), "a best move") : null,
        h("span", { text: `Board ${board}${expected.kind ? `, ${expected.kind}` : ""}` }),
      ),
      details.constraints
        ? disclosure(
            { summary: `Checks: ${details.constraints.filter((c) => c.ok).length} of ${details.constraints.length} hold`, className: "ttt-text" },
            checks(details.constraints),
          )
        : null,
    );
  },
};
