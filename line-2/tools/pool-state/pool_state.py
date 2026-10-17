#!/usr/bin/env python3
"""Decode the proven ZTO/IMD Uniswap v4 slot0, offline and without floats."""
import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'header_anchor_for_pool_state', HERE.parent / 'header-anchor' / 'anchor.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
w = a.w

POOL_ID = '0x888b07bd282f587d3c6b0fcb23e7fc55bbb33abe8910dd7492db815dc8dc5592'
ZTO = '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'
IMD = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
MIN_SQRT = 4295128739
MAX_SQRT = 1461446703485210103287273052203988822378723970342


def pool_slot():
    """StateLibrary: keccak256(abi.encode(poolId, uint256(6)))."""
    return w.hex0(w.keccak256(w.hex_data(POOL_ID, 32) + (6).to_bytes(32, 'big')))


def ratio(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def decode_word(word):
    """Layout interpretation only; callers must prove the word before using it."""
    w.require(type(word) is int and 0 <= word < 1 << 256, 'slot0 must be uint256')
    w.require(word >> 232 == 0, 'nonzero reserved slot0 bits: unsupported layout')
    sqrt = word & ((1 << 160) - 1)
    tick = (word >> 160) & 0xffffff
    if tick & (1 << 23):
        tick -= 1 << 24
    protocol = (word >> 184) & 0xffffff
    fee01, fee10 = protocol & 0xfff, protocol >> 12
    lp_fee = (word >> 208) & 0xffffff
    w.require(MIN_SQRT <= sqrt < MAX_SQRT, 'uninitialized or out-of-range sqrt price')
    w.require(-887272 <= tick <= 887272, 'tick outside v4 range')
    w.require(fee01 <= 1000 and fee10 <= 1000, 'protocol fee outside v4 range')
    w.require(lp_fee == 12500, 'LP fee differs from assigned static-fee pool')
    # Currency order is ascending by address: IMD is currency0, ZTO currency1.
    # No token decimals are assumed; these are ratios of indivisible raw units.
    zto_per_imd = Fraction(sqrt * sqrt, 1 << 192)
    return {
        'sqrtPriceX96': str(sqrt), 'tick': tick,
        'protocolFee0To1Millionths': fee01,
        'protocolFee1To0Millionths': fee10, 'lpFeeMillionths': lp_fee,
        'ztoRawPerImdRaw': ratio(zto_per_imd),
        'imdRawPerZtoRaw': ratio(1 / zto_per_imd),
    }


def verify(header, witness, trusted_hash):
    # Never decode RPC claims, manifest labels or a saved success report directly.
    checked = a.verify(header, witness, trusted_hash, w.POOL_MANAGER, [pool_slot()])
    state = checked['state']
    w.require(state['accountExists'], 'PoolManager account is absent')
    row = state['storage'][0]
    w.require(row['exists'], 'pool slot0 is absent/uninitialized')
    decoded = decode_word(int(row['value'], 16))
    return {
        'verified': True, 'anchor': checked['anchor'],
        'pool': {'manager': state['address'], 'id': POOL_ID, 'slot': pool_slot(),
                 'currency0': IMD, 'currency1': ZTO, 'tickSpacing': 60},
        'provenWord': row['value'], 'decoded': decoded,
        'trust': ('Storage is proven relative to the supplied block hash. Authenticate its '
                  'Ethereum chain, canonicality and finality independently. Pool ID/currency '
                  'binding and deployed v4 layout are assignment assumptions, not proven '
                  'by slot0. Ratios use raw units without decimals; this historical spot '
                  'state is not a swap quote, liquidity proof, TWAP or manipulation-safe oracle.'),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='decode the inherited real ZTO/IMD proof offline')
    check = sub.add_parser('verify', help='verify a new header and exact pool-slot witness')
    check.add_argument('header')
    check.add_argument('witness')
    check.add_argument('--block-hash', required=True)
    args = parser.parse_args(argv)
    try:
        demo = args.command == 'demo'
        header_path = HERE.parent / 'header-anchor/examples/zto-header-mainnet.json' if demo else args.header
        witness_path = HERE.parent / 'state-witness/examples/zto-pool-mainnet.json' if demo else args.witness
        result = verify(a.load_header(header_path), w.load_bundle(witness_path),
                        a.DEMO_HASH if demo else args.block_hash)
        if demo:
            result['demo'] = 'Historical RPC checkpoint observation, not independently authenticated.'
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed header or witness.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
