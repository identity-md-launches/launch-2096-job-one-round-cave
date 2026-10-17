#!/usr/bin/env python3
"""Make deterministic, hash-bound receipts for offline corpus changes.

The input snapshots use Evidence Search's validated index format.  This tool
does not read the original corpus or execute document contents; it compares the
embedded, SHA-256-checked source bytes already carried by the two snapshots.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_engine_path = Path(__file__).absolute().parents[1] / "evidence-search" / "search.py"
_spec = importlib.util.spec_from_file_location("evidence_search", _engine_path)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)

FORMAT = "evidence-corpus-change-receipt/v1"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def citation(document):
    """Return an exact inclusive citation covering the document's source lines."""
    count = len(engine.source_lines(document["text"]))
    return f"{document['path']}:1-{max(1, count)}"


def entry(document):
    return {"path": document["path"], "sha256": document["sha256"], "citation": citation(document)}


def receipt(before, after):
    """Compare two validated snapshots in path order, without timestamps."""
    engine.validate_index(before)
    engine.validate_index(after)
    old = {document["path"]: document for document in before["documents"]}
    new = {document["path"]: document for document in after["documents"]}
    added = [entry(new[path]) for path in sorted(new.keys() - old.keys())]
    removed = [entry(old[path]) for path in sorted(old.keys() - new.keys())]
    changed = [
        {"path": path, "before": entry(old[path]), "after": entry(new[path])}
        for path in sorted(old.keys() & new.keys())
        if old[path]["sha256"] != new[path]["sha256"]
    ]
    body = {"format": FORMAT, "before_documents": len(old), "after_documents": len(new),
            "added": added, "removed": removed, "changed": changed}
    body["receipt_sha256"] = hashlib.sha256(canonical(body)).hexdigest()
    return body


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("make", help="compare two Evidence Search index JSON files")
    make.add_argument("before_index")
    make.add_argument("after_index")
    commands.add_parser("demo", help="compare bundled historical ZTO evidence in memory")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            root = _engine_path.parent / "examples" / "docs"
            before = engine.build_index(root)
            after = json.loads(json.dumps(before))
            after["documents"].append({"path": "handoff.md", "text": "ZTO evidence carried forward.\n",
                                       "sha256": hashlib.sha256(b"ZTO evidence carried forward.\n").hexdigest()})
            after["documents"].sort(key=lambda item: item["path"])
            result = receipt(before, after)
        else:
            result = receipt(engine.load_index(args.before_index), engine.load_index(args.after_index))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (engine.SearchError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
