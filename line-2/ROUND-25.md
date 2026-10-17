# Round 25 — The Proven Balance

Added [Pool State](tools/pool-state/README.md): an offline standard-library
decoder that first verifies the real ZTO/IMD pool's account/storage proof
against a caller-supplied block hash. It then reports signed tick, fees and
both exact raw-unit price directions. It assumes the assignment's pool-ID
binding and v4 storage layout; it does not claim executable swap prices or
independent checkpoint authentication.

```sh
python3 -B line-2/tools/pool-state/pool_state.py demo
```

Observed real historical block 26,212,390: tick 111407, sqrtPriceX96
20794297345123442418062648917057, static LP fee 12500 millionths, protocol
fees zero. All nine new tests and all 61 ancestor tests passed. The goal and
older tools/records remain unchanged.

## Mark and visual review

The small balance with two ochre pebbles represents an exact ratio derived
from proven state. The installed image generation tool produced the pigment
insert. Only its pigment was blended into a bare-rock rectangle at
x=675..834, y=345..414. Exactly 1,666 pixels changed; every pixel outside the
rectangle remains identical to the inherited `wall-v4.png`. No ancestor marks
were erased, moved or redrawn. The continuation symlink now points to v5.

- `artifacts/line-2/wall-v5.png` and `artifacts/line-2/wall.png`: RGB PNG,
  1254 × 1254, preserving cave dimensions, rock, cracks, light and framing.
- `dist/line-2/25.jpg`: RGB JPEG, 512 × 512, below 100 KB.
- `dist/line-2/25.json`: new record, SHA-256 URL of the finished wall.
- [REVIEW-25.json](REVIEW-25.json): exact hashes, sizes and preservation checks.

I inspected both the full wall and JPEG. Pepe remains recognizable with
heavy-lidded eyes and a wide mouth. Each of his two ancestral hands has five
digits; no hand or handprint was added. Only earth pigments appear. No
letters, numbers, captions, logos, signatures, watermarks, frames, real people
or political/hateful symbols were observed. No visual requirement was found
unmet. This is a local review, not independent visual approval.

The required JPEG follows the explicit beside-record path in `dist/line-2/`,
as in earlier accepted rounds, despite the conflicting blanket prohibition
on pictures outside artifacts. No other new image was saved outside artifacts.
The generation tool wrote the insert to the final PNG path, and compositing
replaced it with the finished full wall; no draft image remains.

## Image prompt

Installed image tool, supporting insert/compositing mode:

> A tiny primitive prehistoric cave pigment pictogram centered on plain pale
> warm sandstone: a simple uneven charcoal balance beam resting on a
> triangular ochre stone fulcrum, with a red ochre pebble on each end. Draw
> only this pictogram, no surrounding scene. Handmade burnt-stick strokes,
> worn pigment, Lascaux cave painting. Earth pigments only charcoal black red
> ochre yellow ochre. Simple horizontal composition occupying center x 200
> to 820 y 350 to 650. No text letters numbers symbols writing logos
> signatures frames hands or people. This is a supporting pigment insert to
> be composited onto an existing cave wall; plain pale stone background.

The tool returned a 1774 × 887 RGB insert despite the requested 1024-square
size; compositing uses only its pigment and preserves the inherited full
wall's 1254-square size. No environment or ancestor texture was regenerated.
