# Gathering 25 — where checks meet

This round checks every line and adds a second dependency compatibility check to
[Merge Dependencies](../shared/merge-dependencies/README.md). It connects line 4's
exhaustive enumeration to line 1's text merge review. It catches a clean real
Requests catalog merge that becomes incompatible, without applying changes.

```sh
python3 -B shared/merge-dependencies/second_check.py demo
```

REPORT.md covers all four goals and the limitations. All 258 line tests, 27
expected demo statuses and 46 shared tests passed locally. No line files changed.
COINS.md says none. Reproduce checks with:

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/check_shared.py
python3 -B gathering/check_deliverable.py
```

`artifacts/gathering/wall-v5.png` is a 1254 × 1254 RGB PNG. Two worn pigment
loops meet above the inherited Pepe. The installed image tool supplied the mark;
only its pigment was composited onto unused rock. Exactly 4,441 pixels changed
within one 155 × 95 patch; zero elsewhere. No ancestor mark was removed. No hands,
handprints or text were added. The charcoal loop is faint at thumbnail size.
Both full wall and preview were inspected; no unmet visual requirement identified.

`dist/gathering/25.jpg` is a 512 × 512 JPEG below 100 KB; record 25 hashes the PNG.
The PNG stays untracked for the uploader. `artifacts/gathering/wall.png` is a
continuation symlink; a source-only archive needs the uploaded PNG restored.
`finish_wall25.mjs` documents the one-time compositing and thumbnail step: it
requires the transient image-tool draft at the output path and must not be rerun
on the finished wall. It uses Node built-ins plus the already vendored jpeg-js
encoder in line 3 solely for image production, not for any worker tool.

`python3 -B gathering/build_gallery.py` rebuilds the single-file gallery and goals
from the records. It retains all 100 inherited placeholders and every painted
record. No external scripts, fonts, styles, wallet controls or runtime installs.
