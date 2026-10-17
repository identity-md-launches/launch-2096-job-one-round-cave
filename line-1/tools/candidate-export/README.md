# Candidate Export

Turn a reviewed, pinned **clean** three-directory merge packet into an actual
UTF-8 candidate tree in a **new, separate directory**. Original files stay intact.
This is a staging operation: inspect and test the result before adopting it.
Python 3.10+ and standard library only; retain the sibling `review-recheck`,
`tree-review`, `merge-review` and `threeway` folders. No network or coin is needed.

From the repository root, one command exercises real filesystem exports and
rejections in disposable workspace scratch directories:

```sh
python3 -B line-1/tools/candidate-export/test_export.py
```

All 11 integration tests passed when tried. They include exact CRLF, UTF-8 and
empty-file preservation, nested additions, deletion omission, unchanged inputs,
existing-output refusal, retained-pin mismatch, stale sources, rehashed candidate
tampering, unresolved conflicts, workspace boundaries, symlinks, simulated disk
failure rollback, an empty result and command-line export. All 74 ancestor tests
also passed unchanged. `--demo` prints an in-memory preview without writing files:

```sh
python3 -B line-1/tools/candidate-export/export.py --demo
```

## Export a real reviewed packet

First create and inspect a Tree Review JSON packet, using the existing tool.
Keep the packet outside all three input trees. Independently retain the exact
packet's SHA-256 after review. Then run:

```sh
python3 -B line-1/tools/candidate-export/export.py PACKET.json BASE_DIR OURS_DIR THEIRS_DIR NEW_OUTPUT_DIR --expected-sha256 RETAINED_LOWERCASE_SHA256
```

Replace the capitalized arguments with real workspace paths and the retained
64-digit hash. This command creates `NEW_OUTPUT_DIR`; its parent must already
exist. It refuses any existing output, including an empty directory or symlink,
and any output inside an input tree. Paths must remain inside the current working
workspace and contain no parent traversal or symlink components. Run from the
workspace root. Inputs and output parent must be stable and trusted during use.

Before creating output, the exporter checks the exact packet pin and recomputes
the **entire** review from the current inputs. Every packet field must match,
and there must be no text, delete/modify or path conflicts. It writes only the
recomputed candidates with exclusive file creation, preserving their exact UTF-8
bytes, then rereads and checks the staged tree. Deleted files are absent from the
new directory; no original file is deleted. Empty directories are not reproduced.
A catchable write/verification failure removes the newly created output tree.
An existing output tree is never removed or overwritten.

Successful stdout is a `candidate-export/v1` JSON receipt containing the exact
packet hash, output path, exported manifest, per-file byte counts/SHA-256 values,
omitted deletion paths and limits. Keep that receipt outside the output tree if
you want the manifest to continue describing exactly the exported tree. Error
messages are quoted against terminal control characters. No partial receipt is
printed for rejected exports.

Exit **0**: candidate exported (or preview printed); **1**: valid packet is stale,
altered or conflicted; **2**: invalid arguments, hash, paths, input or filesystem
failure. A hash mismatch is 2. A rehashed altered review is still rejected as 1.

## What happened on real repository files

An extra trial used copies of all six inherited Threeway files. Independent README
edits merged, every unedited source/example byte survived, and the receipt matched
the exported manifest. A second export refused the existing directory, a subsequent
source change refused a new export, and all original inputs stayed unchanged by
export. See `../../REAL-TRIAL-25.json` for observed counts and hashes.

## Limits

Clean text does not imply semantic correctness or approval. A pin received with
an untrusted packet is not independent authentication. Export reuses the ancestor
merge implementation and cannot detect bugs shared by it. No binaries, renames,
permissions, executable bits, author authentication or conflict resolution.

Inherited bounds apply to inputs and the resulting tree: 128 files, 256 directories,
16 levels, 1 MiB/4,000 lines per file, 8 MiB total input text, and a 64 MiB packet.
A clean merge whose output exceeds the single-tree bounds is refused during output
verification and cleaned up. No atomic filesystem snapshot, concurrent path
replacement protection, atomic publication or crash durability is provided.
A killed process can leave partial output: discard it and choose a new destination
before retrying. Do not run against directories being modified concurrently.
The tool reads only supplied workspace inputs and writes only its new destination.
