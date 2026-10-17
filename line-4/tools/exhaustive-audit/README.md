# Exhaustive Audit

Check a small finite dependency catalog by enumerating all candidate version
assignments, using a different search from Offline Resolver. A worker can use this
as a second check on an impossible-catalog claim rather than trusting the original
resolver's representative failed branch.

From the repository root, run:

```sh
python3 -B line-4/tools/exhaustive-audit/audit.py demo
```

This works offline with Python 3.9+ and only the standard library. In this round
it checked **all 24 assignments** for the inherited real Requests release-metadata
projection and returned a verified demonstration of incompatibility. Requests
2.25.1 needs idna below 3; the supplied roots require idna at least 3.10.
No new metadata, network, package installation or package execution is required.

Keep the adjacent `offline-resolver/` and `conflict-core/` folders. The tool imports
Offline Resolver's workspace-bound JSON loader, name/version grammar and catalog
validator. It **never calls its solver or compatibility predicate**. The stored
demo catalog and original source provenance are in Conflict Core's `examples/`.

## Check a catalog or saved claim

Inputs use the existing resolver's `packages` / `roots` JSON format, with numeric
versions and `*`, `==`, `!=`, `<`, `>`, `<=`, `>=` conjunctions. They must be within
the current workspace; duplicate JSON keys and outside paths are rejected by the
shared loader. For example, from the repository root:

```sh
python3 -B line-4/tools/exhaustive-audit/audit.py line-4/tools/conflict-core/examples/requests-conflict.json
```

This direct incompatible-catalog check exits **1**, as expected. A compatible
catalog exits 0 and includes a checked reachable assignment. Invalid input exits
2. An exhausted budget exits **3**, with `status: inconclusive`; it makes no
impossibility claim. `demo` wraps successful exhaustion as a demonstration and
exits 0. Candidate enumeration is deterministic, in sorted package and ascending
numeric version order. It may choose different versions from the original solver.

Add `--max-assignments N` (1–1,000,000; default 10,000) to bound complete
assignments checked. `demo --max-assignments 1` returns inconclusive. Exactly
finishing the enumeration at the limit still establishes impossibility. An empty
root domain proves impossibility with zero complete assignments checked.

Add `--report path/to/report.json` to check a saved resolver or Conflict Core
report's compatibility claim **against the entire supplied catalog**. A resolved
report must supply exactly its reachable `selected` versions and satisfy every
edge. An unsatisfiable report triggers fresh exhaustive enumeration; a discovered
solution rejects the claim with a counterexample (exit 1). A verified claim exits
0. Inconclusive/unknown reports are not accepted as claims.

This mode certifies only compatibility or impossibility for the explicitly
supplied input. It does not authenticate or bind the saved report to its original
catalog: report digests, roots, core, minimality, history and diagnostic fields are
not audited. In particular, it does not independently audit core irreducibility.
To check just a core, supply a separate catalog whose roots are that core.

## Why enumeration covers every solution

The tool collects the union of dependencies from **all releases** transitively
reachable from the roots. Root domains contain all releases matching their root
constraint. Other domains contain every release plus an absent option, including
missing packages. The Cartesian product therefore contains every valid reachable
assignment. Each tuple is checked iteratively from the roots against every
reachable dependency; unreachable releases are ignored and omitted from results.
Cycles terminate through a visited set, while all incoming constraints are still
checked. Requirements of an unselected release cannot invalidate a solution.

This simple approach is exponential and can repeat the same reachable solution
with different irrelevant choices. It intentionally trades speed for a distinct,
small implementation. The budget limits tuples checked, not parsing, graph
construction, edge checks, memory or wall-clock time. The inherited input bounds
still apply. A completed exhaustive run is an observation from this implementation,
not a portable proof certificate, formal verification or independent certification.
It shares parsing/validation with the original solver, so parser bugs remain a
common trust dependency.

Finite-catalog compatibility does not establish installability, publisher trust,
security or completeness of the available releases. This is not full PEP 440;
platform/interpreter markers, extras and artifact hashes remain outside scope.
Adding releases can change an impossible catalog into a compatible one.

## Checks performed

```sh
python3 -B -m unittest discover -s line-4/tools/exhaustive-audit -p 'test_*.py' -v
```

All 14 tests passed, including 500 seeded comparisons with the inherited solver,
cyclic/missing/unreachable dependencies, abandoned branches, comparison operators,
budget boundaries, false claims, malformed assignments, deterministic immutable
inputs, real metadata and CLI exit codes. A test disables the original solver and
compatibility predicate to check that enumeration remains independent of them.
The comparisons are local regression evidence, not independent certification.
