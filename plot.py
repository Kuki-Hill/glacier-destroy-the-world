# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib"]
# ///

"""
Read data/glacier-mass-balance-reference-glaciers.csv, build a tower one brick
per year, and save an animation of it losing its footing to out/.

    uv run plot.py

Every visual property of every brick comes from that year's own row - nothing
is decorative:

  lean (how far the brick sits from the vertical)  <- that year's CUMULATIVE
                                                        mass balance
  notch (how much is bitten out of its base edge)  <- that year's OWN loss,
                                                        cumulative[i]-cumulative[i-1]
  color (how dark the brick is)                    <- the same annual loss,
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
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle

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
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"

BRICK_W = 1.0
BRICK_H = 1.0
MAX_LEAN = 4.0          # brick-widths the tower leans at its worst year - an artistic scale, not a unit conversion
NOTCH_MAX_FRAC = 0.75   # largest bite, as a fraction of a brick's width
FRAMES_PER_YEAR = 4
SHAKE_MAX = 0.45        # brick-widths of sway at the top brick, at the worst year's severity


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
    """One year's brick: where it sits, how bitten it is, how dark it is."""
    lean = abs(cum) / max_abs_cum * MAX_LEAN
    delta = cum - prev_cum
    severity = abs(delta) / max_abs_delta if max_abs_delta else 0.0
    notch = severity * NOTCH_MAX_FRAC * BRICK_W
    x_right = lean + BRICK_W
    x_left = x_right - (BRICK_W - notch)
    y_bottom = i * BRICK_H
    return {
        "x_left": x_left, "width": x_right - x_left,
        "y_bottom": y_bottom, "severity": severity, "lean": lean,
    }


def draw_tower(ax, bricks, cmap, x_offsets=None):
    """Draw every brick in `bricks`, each nudged sideways by x_offsets[i] (or 0)."""
    ax.clear()
    for i, b in enumerate(bricks):
        dx = x_offsets[i] if x_offsets else 0.0
        ax.add_patch(Rectangle(
            (b["x_left"] + dx, b["y_bottom"]), b["width"], BRICK_H,
            facecolor=cmap(b["severity"]), edgecolor=INK, linewidth=0.4, alpha=0.95,
        ))
    top = len(bricks)
    ax.set_xlim(-1.5, MAX_LEAN + BRICK_W + 1.5)
    ax.set_ylim(0, max(top, 1) + 1)
    ax.set_facecolor(SURFACE)
    ax.set_xlabel("instability - brick-widths leaned off vertical", color=MUTED)
    ax.set_ylabel("year built (1956 at the base)", color=MUTED)
    ax.tick_params(colors=MUTED)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.axvline(0, color=MUTED, linewidth=0.8, linestyle=":")


def shake_offsets(top_index, severity, frac):
    """Sideways nudge for every brick 0..top_index, this sub-frame.

    Amplitude comes from `severity` (that year's annual loss, real data).
    Higher bricks sway more (height_frac); the wobble decays across the
    year's sub-frames (frac: 1.0 -> 0.0) so the tower settles before the
    next brick lands. The decay curve and the fact that height amplifies
    sway are artistic structure layered on a data-driven amplitude - the
    README says so.
    """
    import math
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

    # still frame: the finished, settled tower
    fig, ax = plt.subplots(figsize=(6, 9))
    fig.patch.set_facecolor(SURFACE)
    draw_tower(ax, bricks, cmap)
    ax.set_title(f"The Melting Tower - {years[0]}-{years[-1]} reference-glacier mass balance", color=INK)
    fig.tight_layout()
    fig.savefig(OUT / PICTURE, dpi=150, facecolor=SURFACE)
    print(f"saved out/{PICTURE}")
    plt.close(fig)

    # animation: brick by brick, each landing shakes the tower so far
    fig, ax = plt.subplots(figsize=(6, 9))
    fig.patch.set_facecolor(SURFACE)
    total_frames = len(bricks) * FRAMES_PER_YEAR

    def frame(f):
        year_i = f // FRAMES_PER_YEAR
        sub = f % FRAMES_PER_YEAR
        shown = bricks[:year_i + 1]
        decay = 1.0 - sub / FRAMES_PER_YEAR
        offsets = shake_offsets(year_i, shown[-1]["severity"], decay)
        draw_tower(ax, shown, cmap, offsets)
        ax.set_title(f"The Melting Tower - year {years[year_i]}", color=INK)
        fig.tight_layout()

    anim = FuncAnimation(fig, frame, frames=total_frames, interval=1000 / 12)
    anim.save(OUT / GIF, writer=PillowWriter(fps=12))
    print(f"saved out/{GIF}")
    plt.close(fig)


if __name__ == "__main__":
    main()
