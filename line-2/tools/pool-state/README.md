# Pool State

Read the ZTO/IMD Uniswap v4 pool's **proven** slot0 as a tick, directional
protocol fees, LP fee, and exact spot-price ratios. The tool verifies the header
and Ethereum account/storage proof first; it never decodes an unverified RPC
claim or trusts an earlier saved success report.

Run from the repository root, offline, with Python 3.9+ standard library only:

```sh
python3 -B line-2/tools/pool-state/pool_state.py demo
```

Keep sibling `header-anchor/` and `state-witness/` beside this folder. There are
no packages to install and no runtime network calls, keys, wallets, signing,
transactions, payments or deployment.

## What happened when tried

On 2026-10-17 the real inherited mainnet fixture verified at block **26,212,390**,
hash `0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc`.
It decoded `sqrtPriceX96 = 20794297345123442418062648917057`, tick **111407**,
LP fee **12500** millionths (1.25%), and **zero** protocol fees in both
directions. This is historical data, with no claim of freshness. The fixed
demo checkpoint is an inherited RPC observation, not independent consensus
authentication. Inherited public source: <https://ethereum-rpc.publicnode.com>.

The returned `ztoRawPerImdRaw` is exactly `sqrtPriceX96² / 2¹⁹²`, reduced to
integer numerator/denominator strings; `imdRawPerZtoRaw` is its reciprocal.
IMD is currency0 and ZTO currency1 by ascending address order. These are **raw
units**, not human token amounts. No decimals are guessed or fetched. To convert
a raw currency1/currency0 ratio to whole-token units, multiply it by
`10**decimals0 / 10**decimals1`, using separately established decimals.

All nine new tests passed, exercising the real proof and exact reciprocal
arithmetic, wrong checkpoint/header/slot/address/value, missing proof nodes,
extra slots, ignored unproven labels, signed tick decoding, directional fee
packing, malformed words and CLI success/failure output:

```sh
python3 -B -m unittest discover -s line-2/tools/pool-state -p 'test_*.py' -v
```

The signed tick and nonzero directional fees use explicitly synthetic
layout-only test vectors; the demonstration uses the real inherited proof.

## Verify a new observation

Provide a header-only JSON object and `state-witness/1` bundle in the existing
sibling formats. The bundle must prove exactly the assigned PoolManager's
pool slot0. Supply a block hash authenticated independently of that provider:

```sh
python3 -B line-2/tools/pool-state/pool_state.py verify \
  line-2/tools/header-anchor/examples/zto-header-mainnet.json \
  line-2/tools/state-witness/examples/zto-pool-mainnet.json \
  --block-hash 0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc
```

That command reproduces the historical demo. Replace both files and checkpoint
for a new observation. Input files must resolve inside the current workspace;
the sibling bounded loaders reject oversized files, duplicate JSON keys and
malformed proofs. Exit 0 prints one completed JSON report. Verification/input
failure exits 1 with an error JSON on stderr and no stdout; argument errors
exit 2. Neither inputs nor outputs are written by this tool.

## Layout and trust limits

Pool ID and manager come from the assignment. The storage key is computed as
`keccak256(poolId || uint256(6))`, with both operands padded to 32 bytes:
`0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b`.
Slot0's low-to-high fields are 160-bit sqrt price, signed 24-bit tick, two
12-bit directional protocol fees, 24-bit LP fee, then 24 reserved bits.
Nonzero reserved bits, absent/uninitialized state, invalid price/tick/fee
ranges, or an LP fee other than the assigned static **12500** fail closed.
The tick is decoded, not recomputed from the square-root price; no assumption
that tick is a multiple of the position tick spacing is made.

Consulted read-only upstream references:
[StateLibrary](https://github.com/Uniswap/v4-core/blob/main/src/libraries/StateLibrary.sol)
defines `POOLS_SLOT = bytes32(uint256(6))` and the storage key;
[Slot0](https://github.com/Uniswap/v4-core/blob/main/src/types/Slot0.sol) documents:
"24 bits empty | 24 bits lpFee | 12 bits protocolFee 1->0 | 12 bits protocolFee 0->1 | 24 bits tick | 160 bits sqrtPriceX96".
These are documentation references, not runtime dependencies.

The proof commits to bytes. The assignment's pool-ID/currency binding and the
deployed PoolManager's v4 layout remain explicit interpretation assumptions;
this tool does not prove the pool key preimage, manager bytecode or storage
layout from those bytes. The caller must authenticate the checkpoint's chain,
canonicality and finality. A spot ratio provides no liquidity, executable swap
quote, TWAP, slippage bound or manipulation resistance. Nothing here should
authorize a payment automatically. No additional coin is required.
