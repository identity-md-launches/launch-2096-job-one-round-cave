import contextlib
import copy
from fractions import Fraction
import importlib.util
import io
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pool_state_tested', HERE / 'pool_state.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PoolStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.header = p.a.load_header(HERE.parent / 'header-anchor/examples/zto-header-mainnet.json')
        cls.bundle = p.w.load_bundle(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json')

    def verify(self, header=None, bundle=None, checkpoint=None):
        return p.verify(self.header if header is None else header,
                        self.bundle if bundle is None else bundle,
                        p.a.DEMO_HASH if checkpoint is None else checkpoint)

    def test_real_pool_and_exact_reciprocals(self):
        before = copy.deepcopy((self.header, self.bundle))
        result = self.verify()
        self.assertEqual(int(result['anchor']['blockNumber'], 16), 26212390)
        self.assertEqual(result['decoded']['sqrtPriceX96'], '20794297345123442418062648917057')
        self.assertEqual(result['decoded']['tick'], 111407)
        self.assertEqual(result['decoded']['lpFeeMillionths'], 12500)
        self.assertEqual(result['decoded']['protocolFee0To1Millionths'], 0)
        self.assertEqual(result['decoded']['protocolFee1To0Millionths'], 0)
        ratios = result['decoded']
        first = ratios['ztoRawPerImdRaw']
        second = ratios['imdRawPerZtoRaw']
        q = Fraction(int(first['numerator']), int(first['denominator']))
        inv = Fraction(int(second['numerator']), int(second['denominator']))
        self.assertEqual(q * inv, 1)
        self.assertEqual(q, Fraction(20794297345123442418062648917057 ** 2, 2 ** 192))
        self.assertEqual((self.header, self.bundle), before)

    def test_slot_derivation_and_order(self):
        self.assertEqual(p.pool_slot(), p.a.POOL_SLOT)
        self.assertLess(int(p.IMD, 16), int(p.ZTO, 16))

    def test_changed_checkpoint_and_header_fail(self):
        with self.assertRaises(p.w.Invalid):
            self.verify(checkpoint='0x' + '11' * 32)
        header = copy.deepcopy(self.header)
        header['stateRoot'] = '0x' + '11' * 32
        with self.assertRaises(p.w.Invalid):
            self.verify(header=header)

    def test_wrong_slot_address_or_value_fail(self):
        for field in ('address', 'key', 'value'):
            bundle = copy.deepcopy(self.bundle)
            if field == 'address':
                bundle['proof'][field] = p.ZTO
            else:
                bundle['proof']['storageProof'][0][field] = '0x1'
            with self.subTest(field=field), self.assertRaises(p.w.Invalid):
                self.verify(bundle=bundle)

    def test_missing_nodes_and_extra_slots_fail(self):
        bundle = copy.deepcopy(self.bundle)
        bundle['proof']['storageProof'][0]['proof'] = []
        with self.assertRaises(p.w.Invalid):
            self.verify(bundle=bundle)
        bundle = copy.deepcopy(self.bundle)
        bundle['proof']['storageProof'].append(copy.deepcopy(bundle['proof']['storageProof'][0]))
        with self.assertRaises(p.w.Invalid):
            self.verify(bundle=bundle)

    def test_unproven_labels_not_used(self):
        bundle = copy.deepcopy(self.bundle)
        bundle.update(block='invented', chainId=99, address=p.ZTO, slots=['0x0'])
        self.assertEqual(self.verify(bundle=bundle), self.verify())

    def test_signed_tick_and_directional_fee_layout(self):
        # Synthetic layout-only test, never advertised as a real proof.
        word = (12500 << 208) | (((999 << 12) | 17) << 184) | ((2 ** 24 - 1) << 160) | (1 << 96)
        decoded = p.decode_word(word)
        self.assertEqual(decoded['tick'], -1)
        self.assertEqual(decoded['protocolFee0To1Millionths'], 17)
        self.assertEqual(decoded['protocolFee1To0Millionths'], 999)
        self.assertEqual(decoded['imdRawPerZtoRaw'], {'numerator': '1', 'denominator': '1'})

    def test_invalid_words_fail(self):
        base = (12500 << 208) | (1 << 96)
        bad = [-1, 1 << 256, True, 0, base | (1 << 232),
               (12499 << 208) | (1 << 96), base | (1001 << 184),
               base | (1001 << 196), base | (887273 << 160),
               (12500 << 208) | (p.MIN_SQRT - 1), (12500 << 208) | p.MAX_SQRT]
        for word in bad:
            with self.subTest(word=word), self.assertRaises(p.w.Invalid):
                p.decode_word(word)

    def test_cli_success_and_fail_closed(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = p.main(['demo'])
        self.assertEqual(status, 0)
        self.assertEqual(err.getvalue(), '')
        self.assertTrue(json.loads(out.getvalue())['verified'])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = p.main(['verify', str(HERE.parent / 'header-anchor/examples/zto-header-mainnet.json'),
                             str(HERE.parent / 'state-witness/examples/zto-pool-mainnet.json'),
                             '--block-hash', '0x' + '11' * 32])
        self.assertEqual(status, 1)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(json.loads(err.getvalue())['verified'])


if __name__ == '__main__':
    unittest.main()
