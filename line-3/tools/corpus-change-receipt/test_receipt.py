import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from contextlib import redirect_stderr, redirect_stdout

_path = Path(__file__).with_name("receipt.py")
_spec = importlib.util.spec_from_file_location("change_receipt", _path)
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)


def index(*documents):
    return {"format": tool.engine.FORMAT, "documents": [
        {"path": path, "text": text, "sha256": hashlib.sha256(text.encode()).hexdigest()}
        for path, text in documents]}


class ReceiptTests(unittest.TestCase):
    def test_added_removed_changed_are_sorted_and_cited(self):
        result = tool.receipt(index(("z.md", "old\n"), ("gone.md", "bye\n")),
                              index(("z.md", "new\nnext\n"), ("a.md", "hello\n")))
        self.assertEqual([x["path"] for x in result["added"]], ["a.md"])
        self.assertEqual([x["path"] for x in result["removed"]], ["gone.md"])
        self.assertEqual(result["changed"][0]["before"]["citation"], "z.md:1-1")
        self.assertEqual(result["changed"][0]["after"]["citation"], "z.md:1-2")

    def test_deterministic_hash_and_unchanged_snapshots(self):
        before = index(("z.md", "same\n"))
        first = tool.receipt(before, index(("z.md", "same\n")))
        second = tool.receipt(before, index(("z.md", "same\n")))
        self.assertEqual(first, second)
        self.assertEqual(first["added"] + first["removed"] + first["changed"], [])
        self.assertEqual(len(first["receipt_sha256"]), 64)

    def test_forged_hash_rejected(self):
        bad = index(("z.md", "true\n"))
        bad["documents"][0]["sha256"] = "0" * 64
        with self.assertRaises(tool.engine.SearchError):
            tool.receipt(bad, bad)

    def test_demo_and_cli_error(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            status = tool.main(["demo"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out.getvalue())["added"][0]["path"], "handoff.md")
        with redirect_stdout(out := io.StringIO()), redirect_stderr(err := io.StringIO()):
            status = tool.main(["make", "missing.json", "also-missing.json"])
        self.assertEqual(status, 2)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("not a regular file", json.loads(err.getvalue())["error"])


if __name__ == "__main__":
    unittest.main()
