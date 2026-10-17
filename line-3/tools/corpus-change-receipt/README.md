# Corpus Change Receipt

Compare two offline Evidence Search snapshots and return a deterministic receipt
of added, removed, and byte-changed documents. Every listed item includes its
SHA-256 and an exact inclusive source-line citation. This lets a worker explain
what evidence changed before it repeats a cited search. Python 3.9+ and the
standard library only; no network, document execution, writes, keys, or
transactions.

From the repository root, this one command runs a read-only demonstration using
the bundled historical ZTO-first evidence and an in-memory handoff document:

```sh
python3 -B line-3/tools/corpus-change-receipt/receipt.py demo
```

When tried, it reported one addition, `handoff.md:1-1`, and a stable receipt
SHA-256. To compare snapshots you already made with Evidence Search:

```sh
python3 -B line-3/tools/corpus-change-receipt/receipt.py make before-index.json after-index.json
```

Both snapshots are validated before comparison: malformed envelopes, duplicate
paths, unsafe names, oversized content and source bytes that do not match their
declared SHA-256 fail closed. The receipt hash is SHA-256 over canonical JSON of
the receipt body (without `receipt_sha256`), so formatting does not affect it.
Document-level citations identify the complete changed source, not the semantic
meaning of a change. Hashes establish byte identity, not truth, authorship,
remote freshness, or a current ZTO/IMD chain state.

Checks run:

```sh
python3 -B line-3/tools/corpus-change-receipt/test_receipt.py -v
```

The tool itself is Python standard library only. A small vendored copy of
`jpeg-js` (MIT license) is present solely for the one-time JPEG wall export; it
is not imported, needed, or run by this receipt tool.
