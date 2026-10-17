"""Integration checks for safe candidate export; standard library only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('candidate_export', HERE / 'export.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class ExportTests(unittest.TestCase):
    def setUp(self):
        scratch = Path.cwd() / 'test' / 'scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.inputs = [self.root / s for s in e.r.tree.SIDES]
        for p in self.inputs:
            p.mkdir()
            (p / 'note.txt').write_bytes(b'first\r\nsecond\r\n')
            (p / 'remove.txt').write_bytes(b'remove\n')
        (self.inputs[1] / 'note.txt').write_bytes(b'ours\r\nsecond\r\n')
        (self.inputs[2] / 'note.txt').write_bytes(b'first\r\ntheirs\r\n')
        (self.inputs[2] / 'remove.txt').unlink()
        (self.inputs[1] / 'nested').mkdir()
        (self.inputs[1] / 'nested' / 'new.txt').write_bytes('café'.encode())
        (self.inputs[1] / 'empty.txt').write_bytes(b'')
        self.packet = self.root / 'packet.json'
        self.output = self.root / 'exported'
        self.pin()

    def pin(self):
        self.packet.write_text(json.dumps(e.r.tree.from_directories(self.inputs)))
        self.digest = hashlib.sha256(self.packet.read_bytes()).hexdigest()

    def run_export(self, **kwargs):
        args = dict(packet_path=self.packet, inputs=self.inputs,
                    output=self.output, expected_sha256=self.digest)
        args.update(kwargs)
        return e.export(**args)

    def test_roundtrip_exact_bytes_and_input_immutability(self):
        before = {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = self.run_export()
        self.assertEqual((self.output / 'note.txt').read_bytes(), b'ours\r\ntheirs\r\n')
        self.assertEqual((self.output / 'empty.txt').read_bytes(), b'')
        self.assertEqual((self.output / 'nested/new.txt').read_bytes(), 'café'.encode())
        self.assertFalse((self.output / 'remove.txt').exists())
        self.assertEqual(result['omitted_deletions'], ['remove.txt'])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        for name, info in result['files'].items():
            self.assertEqual(hashlib.sha256((self.output / name).read_bytes()).hexdigest(), info['sha256'])

    def test_refuses_existing_even_empty_output(self):
        self.output.mkdir()
        with self.assertRaises(ValueError):
            self.run_export()
        self.assertTrue(self.output.is_dir())

    def test_refuses_changed_packet_pin(self):
        self.packet.write_bytes(self.packet.read_bytes() + b'\n')
        with self.assertRaises(ValueError):
            self.run_export()
        self.assertFalse(self.output.exists())

    def test_refuses_stale_sources(self):
        (self.inputs[0] / 'new').write_text('stale')
        with self.assertRaises(e.Refused):
            self.run_export()
        self.assertFalse(self.output.exists())

    def test_refuses_rehashed_candidate_tampering(self):
        packet = json.loads(self.packet.read_bytes())
        packet['files'][0]['candidate'] = 'injected'
        self.packet.write_text(json.dumps(packet))
        self.digest = hashlib.sha256(self.packet.read_bytes()).hexdigest()
        with self.assertRaises(e.Refused):
            self.run_export()
        self.assertFalse(self.output.exists())

    def test_refuses_conflicts(self):
        (self.inputs[2] / 'note.txt').write_text('conflicting\r\nsecond\r\n')
        self.pin()
        with self.assertRaises(e.Refused):
            self.run_export()
        self.assertFalse(self.output.exists())

    def test_output_path_boundaries(self):
        link = self.root / 'link'
        link.symlink_to(self.inputs[0], target_is_directory=True)
        dangling = self.root / 'dangling'
        dangling.symlink_to('missing')
        for target in (self.inputs[0] / 'inside', link / 'out', dangling,
                       self.root / '..' / 'out', Path('/tmp/export-out')):
            with self.assertRaises(ValueError, msg=str(target)):
                self.run_export(output=target)

    def test_symlink_source_rejected(self):
        (self.inputs[1] / 'bad').symlink_to('../base/note.txt')
        with self.assertRaises(ValueError):
            self.run_export()
        self.assertFalse(self.output.exists())

    def test_rollback_on_write_failure(self):
        original = Path.open
        def fail(path, mode='r', *args, **kwargs):
            if path.is_relative_to(self.output) and mode == 'xb':
                raise OSError('injected disk failure')
            return original(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', fail):
            with self.assertRaises(OSError):
                self.run_export()
        self.assertFalse(self.output.exists())

    def test_empty_result(self):
        for folder in self.inputs:
            for child in sorted(folder.rglob('*'), reverse=True):
                child.rmdir() if child.is_dir() else child.unlink()
        self.pin()
        result = self.run_export()
        self.assertEqual(result['files'], {})
        self.assertEqual(list(self.output.iterdir()), [])

    def test_cli_required_pin_and_real_export(self):
        command = [sys.executable, '-B', str(HERE / 'export.py'), str(self.packet),
                   *map(str, self.inputs), str(self.output)]
        bad = subprocess.run(command, capture_output=True)
        self.assertEqual(bad.returncode, 2)
        self.assertFalse(self.output.exists())
        good = subprocess.run(command + ['--expected-sha256', self.digest], capture_output=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)['schema'], 'candidate-export/v1')


if __name__ == '__main__':
    unittest.main()
