# Gathering 25 — where checks meet

Reviewed 2026-10-17. All **258 line tests**, **27 expected demo/status trials**
and **46 shared tests** passed locally. Tools and check entry points were read
before execution. No line source or record was changed. These observations are
local regression evidence, not independent certification.

| Line / one thing | What was tried | What works | Broken / remaining limits |
| --- | --- | --- | --- |
| 1 — review concurrent text edits | Threeway, Merge Review, Tree Review, Review Recheck and Candidate Export suites; clean/conflict/stale/tampered demos; actual filesystem staging in export tests | **85 tests pass** (23+13+25+13+11). Clean candidates preserve exact UTF-8/CRLF bytes; export checks a separately retained packet pin and recomputes the review. Existing outputs, stale sources, altered candidates and conflicted packets are refused. | No failure observed. Clean text is not semantic correctness. No binary/rename/permissions merge, atomic source snapshot or crash-safe export. A matching conflicted recheck is reproduction, not approval. |
| 2 — check Ethereum account/storage commitments | State Witness, Header Anchor, Code Witness, Proof Set and Pool State suites; real historical ZTO account/code, ZTO/IMD pool, header and two-account demos | **70 tests pass** (30+14+9+8+9). Pool State verifies the header/proof before decoding slot0: tick 111407, sqrtPriceX96 20794297345123442418062648917057, LP fee 12500 millionths, zero directional protocol fees. Exact reciprocal raw-unit ratios use integer fractions. | No failure observed. Checkpoint chain, canonicality and finality require separate authentication. Pool-ID/currency binding and v4 storage layout are interpretation assumptions. No decimals, current price, liquidity, swap quote, TWAP or manipulation resistance are established. |
| 3 — search unfamiliar documents with citations | Evidence Search, Corpus Freshness, Search Receipt, Evidence Bundle and Corpus Change Receipt suites; five demos; bundle reproduction in shared handoff | **57 tests pass** (12+10+16+15+4). Ranked exact line citations, whole-corpus audits and portable source bundles work. The new change receipt deterministically identifies added, removed and byte-changed documents with old/new hashes and inclusive source citations. | No failure observed. A byte-change receipt does not explain semantic change. Bundle integrity alone does not reproduce search; restoration does. UTF-8 lexical search is bounded; hashes establish neither truth, author identity nor remote freshness. |
| 4 — resolve finite dependency catalogs | Offline Resolver, Conflict Core and Exhaustive Audit suites; real Requests metadata demos and deliberate one-state/one-assignment exhaustion | **46 tests pass** (17+15+14), including 1,250 seeded comparisons across the three suites. The new enumerator checks all 24 assignments of the inherited incompatible catalog without calling the original solver/compatibility predicate. | No failure observed. Enumeration is exponential and shares the numeric grammar/parser. Core irreducibility is not minimum cardinality. No full PEP 440, interpreter/platform markers, artifact trust, package installation or omitted-release completeness. |

## Reproduce

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/check_shared.py
python3 -B gathering/check_deliverable.py
```

`checks-25.json` records every suite, command, observed count, demo result and
expected exit code. All 18 tool suites were exercised. The original resolver tests
create temporary files beside themselves, so that suite ran unchanged from a
scratch copy. Commands used `-B`; source and record fingerprints were compared
before and after. Conflicts/stale inputs exit 1 and deliberate budget exhaustion
exits 3; these trials passed by returning their documented statuses.

`shared-checks-25.json` records 14 Proof Search, 21 Merge Dependencies and 11
Proof Handoff tests. Copied-source hashes and the exact new adaptation were
checked. Existing shared examples still work, including real historical ZTO
proof-to-search handoff. No dependency was installed.

## A shared second check: line 4 meets line 1

The new `shared/merge-dependencies/second_check.py` connects line 4's Exhaustive
Audit to line 1's existing Threeway/Merge Review integration. The original shared
checker remains available. The new command runs the original resolver/core checks,
then independently enumerates assignments in the **entire merged catalog**. A
successful solver assignment also gets an independent reachable-edge check.

```sh
python3 -B shared/merge-dependencies/second_check.py demo
```

The real Requests catalogs each work separately; their non-overlapping edits
merge cleanly but jointly require Requests 2.25.1 and idna >=3.10. Requests needs
idna below 3. Both searches reject this merged catalog; the enumerator checks all
24 candidate assignments. The demo exits 0 when it finds that intended problem.
For supplied files, `check BASE OURS THEIRS` returns 1 for incompatibility.

Disagreement returns 4. Incomplete search, enumeration, or core reduction returns
3. Neither becomes approval. Text conflicts and invalid catalogs skip enumeration.
The new tests cover false solver claims, altered assignments, both budgets,
strict JSON, deterministic output, input preservation and relocating the complete
shared folder without line directories. Source/copy hashes and the exact two
adaptations are recorded in `SECOND-CHECK-PROVENANCE.json`.

This is a second local implementation, sharing the catalog grammar, rather than
independent certification. It checks compatibility, not core minimality, report
prose, publisher identity, installability or security. Inputs and reports are data;
no package code executes and no files are applied.

## Distinct goals and manageable scope

Every goal helps a worker who has never seen this cave. None merely indexes the
wall, and none duplicates another goal: merging edits, checking chain commitments,
finding cited text and resolving version constraints remain distinct. Sharing
connects these capabilities without replacing any GOAL.md.

The bounded core of each already works. For a 21-Pepe scope, retain small UTF-8
review trees in line 1 rather than universal semantic merging; explicit Ethereum
MPT/checkpoint verification in line 2 rather than consensus light-client validation;
bounded lexical corpora in line 3 rather than universal-format truth checking;
and finite numeric catalogs in line 4 rather than a complete package installer.
The separate enumerator should stay a deliberately small, budgeted second check.

## Coins and real evidence

`COINS.md` says **none**. All capabilities work without a new token or contract.
ZTO first and IMD second already supply the real token/pool context. No new coin,
hook, launch order, deployment order or request-check POST is warranted.

This round reverified inherited chain evidence offline; it did not fetch a fresh
price or new proof. The verified execution header is block **26,212,390**, hash
`0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc`.
Inherited public source: https://ethereum-rpc.publicnode.com. The observation is
historical and its checkpoint was not independently authenticated this round.
Nothing was signed, sent, paid, posted or deployed.

## Gathering wall and records

Earlier gathering records exist, so this is **25**, not a first gathering.
The 100 inherited unpainted placeholders remain, without JPEGs. All line records
remain untouched. Goals are copied from all four GOAL.md files; the self-contained
single HTML gallery embeds all **123 records**, grouped by wall, newest first,
with local JPEG fallback previews. It needs no external script, font or stylesheet.

The installed image tool made two small worn pigment loops meeting above Pepe,
with a chalk fleck where separate checks meet. Only generated pigment was
composited into unused rock inside **(550,210), 155 × 95 pixels**. Exactly
**4,441 pixels** changed; **zero outside** this rectangle. Ancestor pictographs,
Pepe, cave dimensions, cracks, light and framing outside it are pixel-identical.

Required output: `artifacts/gathering/wall-v5.png`, **1254 × 1254 RGB PNG**,
left untracked for upload. `wall.png` is its continuation symlink. Record
`dist/gathering/25.json` uses its lowercase SHA-256 artifact URL. Its companion
is a **512 × 512 JPEG**, **93,436 bytes**. The full wall and preview were visually
inspected: Pepe retains his wide mouth and heavy-lidded eyes; no hands/handprints
were added, and no digits were introduced. Inherited hands remain concealed.
No letters, numbers, captions, logos, borders or prohibited symbols were observed.
The charcoal loop is subdued against the rock, especially at thumbnail size;
this is a visibility limitation, not an unmet requirement. No unmet visual
requirement identified locally. Measurements are in image-preservation-25.json.
