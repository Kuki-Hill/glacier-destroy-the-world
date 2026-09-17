# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///

"""
Read data/glacier-mass-balance-reference-glaciers.csv, build a tower one brick
per year in real 3D space, and save an animation of it losing its footing to
out/.

    uv run plot.py

Every geometric property of every brick still comes from that year's own row -
switching from a flat chart to a solid, lit, rotating structure changed nothing
about what drives the shape:

  lean (how far the brick sits from the vertical)  <- that year's CUMULATIVE
                                                        mass balance
  notch (how much is bitten out of its base edge,  <- that year's OWN loss,
         shrinking the block and shifting it out)      cumulative[i]-cumulative[i-1]
  color (how pale-to-deep blue the block glows)     <- the same annual loss,
                                                        as a fraction of the
                                                        worst year on record
  shake (how hard the whole tower shudders when     <- the same annual loss
         this brick lands)                             again

The shake amplitude is not invented: a scratch check against the raw CSV
(kept out of this repo, in ../scratch/) confirmed that the decade-average
*annual* loss climbs roughly monotonically from the 1980s onward (1980s 0.24,
1990s 0.48, 2000s 0.52, 2010s 0.81, 2020s 0.97 m w.e./year) - so "shakes worse
in recent decades" is something the data actually does, not a story imposed on
it. An earlier hypothesis - shake driven by year-over-year *acceleration* of
melt - was checked the same way and rejected: its decade averages do not climb
(peak decade average is the 1960s, peak single year is 1987), so it would have
been decorating a claim the numbers don't support.

The slow camera rotation and the dark void it floats in are pure staging - they
show the same numbers from more angles, they do not add or hide any of them.
"""

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 - registers the 3d projection

FILE = "glacier-mass-balance-reference-glaciers.csv"
GIF = "tower.gif"
PICTURE = "tower.png"

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"

# dataviz skill's validated sequential ramp, one hue (blue), light -> dark,
# steps 100 through 700 (references/palette.md) - lightest reads as "near zero"
BLUE_RAMP = [
    "#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
    "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b",
]
VOID = "#05070a"       # the dark space the tower stands in - not a chart surface
INK = "#c7d3e8"        # cool, muted label color, legible on the void

BRICK_W = 1.0
BRICK_D = 1.2           # depth: bricks are solid blocks, not flat panels
BRICK_H = 1.0
MAX_LEAN = 4.0          # brick-widths the tower leans at its worst year - an artistic scale, not a unit conversion
NOTCH_MAX_FRAC = 0.75   # largest bite, as a fraction of a brick's width
FRAMES_PER_YEAR = 3
SHAKE_MAX = 0.45        # brick-widths of sway at the top brick, at the worst year's severity
TURNS = 1.0             # full camera revolutions over the whole animation - staging, not data
ELEV = 16


def rows(path):
    """The file as (year, cumulative mass balance) pairs, oldest first."""
    kept = []
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["Mean cumulative mass balance"] == "":
                continue
            kept.append((int(row["Year"]), float(row["Mean cumulative mass balance"])))
    return kept


def brick(i, cum, prev_cum, max_abs_cum, max_abs_delta):
    """One year's block: where it sits, how bitten it is, how it glows."""
    lean = abs(cum) / max_abs_cum * MAX_LEAN
    delta = cum - prev_cum
    severity = abs(delta) / max_abs_delta if max_abs_delta else 0.0
    notch = severity * NOTCH_MAX_FRAC * BRICK_W
    x_right = lean + BRICK_W
    x_left = x_right - (BRICK_W - notch)
    return {
        "x_left": x_left, "width": x_right - x_left,
        "z_bottom": i * BRICK_H, "severity": severity, "lean": lean,
    }


def draw_tower(ax, bricks, cmap, azim, x_offsets=None):
    """Draw every block in `bricks` as a solid 3D box, nudged sideways by
    x_offsets[i] (or 0), floating in a dark void with no chart chrome."""
    ax.clear()
    for i, b in enumerate(bricks):
        dx = x_offsets[i] if x_offsets else 0.0
        ax.bar3d(
            b["x_left"] + dx, -BRICK_D / 2, b["z_bottom"],
            b["width"], BRICK_D, BRICK_H,
            color=cmap(b["severity"]), edgecolor=VOID, linewidth=0.3,
            shade=True,
        )

    top = len(bricks)
    lean_now = bricks[-1]["lean"] + bricks[-1]["width"]
    shadow = plt.matplotlib.patches.Ellipse(
        (lean_now / 2, 0), lean_now + BRICK_W, BRICK_D * 1.4,
        facecolor="#0a0e16", alpha=0.6, zorder=-1,
    )
    ax.add_patch(shadow)
    from mpl_toolkits.mplot3d import art3d
    art3d.pathpatch_2d_to_3d(shadow, z=0, zdir="z")

    ax.set_xlim(-1.5, MAX_LEAN + BRICK_W + 1.5)
    ax.set_ylim(-3, 3)
    ax.set_zlim(0, max(top, 1) + 1)
    ax.set_box_aspect((1, 0.6, 2.2))
    ax.view_init(elev=ELEV, azim=azim)
    ax.dist = 8.3
    ax.set_axis_off()
    ax.set_facecolor(VOID)
    ax.patch.set_facecolor(VOID)
    ax.patch.set_alpha(1.0)
    fig = ax.figure
    fig.patch.set_facecolor(VOID)
    ax.set_position([-0.08, -0.03, 1.16, 1.08])


def shake_offsets(top_index, severity, frac):
    """Sideways nudge for every block 0..top_index, this sub-frame.

    Amplitude comes from `severity` (that year's annual loss, real data).
    Higher blocks sway more (height_frac); the wobble decays across the
    year's sub-frames (frac: 1.0 -> 0.0) so the tower settles before the
    next block lands. The decay curve and the fact that height amplifies
    sway are artistic structure layered on a data-driven amplitude - the
    README says so.
    """
    offsets = []
    for j in range(top_index + 1):
        height_frac = j / top_index if top_index else 1.0
        amp = severity * SHAKE_MAX * height_frac * frac
        offsets.append(amp * math.cos(2 * math.pi * 1.5 * frac))
    return offsets


def main():
    table = rows(DATA)
    print(f"{DATA.name}: {len(table)} years, {table[0][0]}-{table[-1][0]}")

    years = [y for y, _ in table]
    cum = [c for _, c in table]
    deltas = [0.0] + [cum[i] - cum[i - 1] for i in range(1, len(cum))]
    max_abs_cum = max(abs(c) for c in cum)
    max_abs_delta = max(abs(d) for d in deltas)
    print(f"cumulative loss: 0 to {min(cum)} m w.e.  worst single year: {max_abs_delta:.3f} m w.e.")

    bricks = []
    for i, (year, c) in enumerate(table):                          # the loop over the numbers
        bricks.append(brick(i, c, cum[i - 1] if i else c, max_abs_cum, max_abs_delta))

    cmap = LinearSegmentedColormap.from_list("glacier_blue", BLUE_RAMP)

    OUT.mkdir(exist_ok=True)

    # still frame: the finished, settled tower, camera angle chosen to show the lean
    fig = plt.figure(figsize=(7, 9))
    ax = fig.add_subplot(projection="3d")
    draw_tower(ax, bricks, cmap, azim=-55)
    fig.text(0.06, 0.95, f"The Melting Tower  ({years[0]}-{years[-1]})",
              color=INK, fontsize=13, family="sans-serif")
    fig.savefig(OUT / PICTURE, dpi=150, facecolor=VOID)
    print(f"saved out/{PICTURE}")
    plt.close(fig)

    # animation: block by block, each landing shakes the tower so far; camera turns throughout
    fig = plt.figure(figsize=(7, 9))
    ax = fig.add_subplot(projection="3d")
    total_frames = len(bricks) * FRAMES_PER_YEAR
    azim_start = -55
    label = fig.text(0.06, 0.95, "", color=INK, fontsize=13, family="sans-serif")

    def frame(f):
        year_i = f // FRAMES_PER_YEAR
        sub = f % FRAMES_PER_YEAR
        shown = bricks[:year_i + 1]
        decay = 1.0 - sub / FRAMES_PER_YEAR
        offsets = shake_offsets(year_i, shown[-1]["severity"], decay)
        azim = azim_start + 360 * TURNS * f / total_frames
        draw_tower(ax, shown, cmap, azim, offsets)
        label.set_text(f"The Melting Tower  -  {years[year_i]}")

    anim = FuncAnimation(fig, frame, frames=total_frames, interval=1000 / 12)
    anim.save(OUT / GIF, writer=PillowWriter(fps=12))
    print(f"saved out/{GIF}")
    plt.close(fig)


if __name__ == "__main__":
    main()
