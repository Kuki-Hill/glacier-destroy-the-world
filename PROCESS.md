# Process

## Tools

I worked through this whole assignment in conversation with Claude Code (an AI
assistant), asking it to research options, check real numbers before I committed
to a design, and write `fetch.py` / `plot.py` from the design we agreed on. What
follows is an honest summary of that conversation, not a cleaned-up version of it.

**Brainstorming.** I started by telling the assistant I did not want it to fetch
any data yet — I wanted to pick the phenomenon myself, through discussion, and
have it give me options first rather than defaulting to something for me.

**First idea, and why it was rejected.** My first real idea was glacier melt and
its impact on land erosion in an island nation — I wanted to show the melt
speeding up and connect it to an island losing land. I asked the assistant to
check whether that data existed. It found real glacier data easily, but when it
checked the island-erosion half, the most-cited quantified study (Kench et al.,
*Nature Communications*, 2018) found that Tuvalu's total land area actually
*grew* by 2.9% over roughly forty years — the opposite of what my intuitive
narrative assumed. The assistant told me this directly instead of quietly using
only the half of the story that fit. Using only the erosion half while ignoring
that finding would have been cherry-picking data to fit a story I already wanted
to tell, so I rejected the island half of the idea entirely.

**The final idea.** I decided to drop the island-nation angle completely and go
fully artistic with just the glacier data itself: a tower built one brick per
year, where each year's real number pulls at the tower's foundation and makes it
more unstable — visually literal, not a metaphor layered on top of unrelated
numbers. I confirmed with the assistant that I wanted this as an animated GIF
(not a static image), and that each brick's color should represent that year's
melt severity, not just how many glaciers were observed.

**A hypothesis I asked for, and rejected once the data didn't support it.** I
also asked for the tower to shake or wobble, but insisted the shake be strictly
constrained by the real data, not just a random or decorative effect. The
assistant's first idea was to drive the shake by how much the melt rate was
*accelerating* year over year. It tested that against the actual CSV by
averaging the acceleration by decade, and the result did not climb over time —
the peak decade average was in the 1960s and the single worst year was 1987, not
anywhere near the present. That contradicted the "getting worse" feeling the
shake was supposed to carry, so we rejected that version rather than fudge the
numbers to make it "look right." The alternative we kept: plain annual loss
(how much a single year lost, not its rate of change) does climb by decade,
fairly steadily, from the 1980s onward. That is the number that now drives the
shake amplitude — the same number already driving each brick's notch width and
color, reused rather than inventing a fourth signal.

**The first render, and why I rejected it.** The first working version rendered
the tower as a flat 2D matplotlib chart — rectangles on an x/y axis with tick
labels and a title, colored by severity. Once I saw it, it read exactly like a
scientific plot, not a piece of art — a research-report look, not the "cool,"
spatial, three-dimensional object I actually wanted. I rejected that rendering
outright and asked for a genuinely spatial, three-dimensional structure instead,
still built strictly from the same numbers. The fix was to switch from flat
rectangles on a 2D chart axis to real solid 3D blocks (`bar3d`), drop every piece
of chart chrome (axes, ticks, gridlines, labels), put the tower in a dark void
instead of a light chart surface, and slowly rotate the camera around it over the
course of the animation. None of the data mappings (lean, notch, color, shake)
changed — only how the same numbers get drawn.

## Kept

- The literal, one-to-one mapping from CSV numbers to every visual property of
  the tower (lean, notch, color, shake) — nothing in the final picture is placed
  by eye.
- The annual-loss-driven shake, after checking its decade averages actually
  climb over time.
- The sequential blue color ramp from the course's own data-visualization
  reference palette, rather than inventing a new color scheme, since severity
  here is a single continuous magnitude and that is exactly what a one-hue
  sequential ramp is for.

## Rejected

- The island-nation erosion narrative — real data (island land area growing,
  not shrinking) contradicted the intuitive story, so it was dropped rather than
  kept and quietly cherry-picked.
- The acceleration-based shake hypothesis — checked against the real CSV by
  decade and found not to climb over time the way the concept needed it to, so
  it was thrown away in favor of the plain annual-loss version, which does.
- The first, flat 2D chart-style render — it looked like a research plot instead
  of an artwork, so it was discarded in favor of the solid, rotating 3D version,
  with every data-to-geometry mapping carried over unchanged.
