# modbus-frame-ledger

Decode one captured Modbus RTU register response against an explicit typed CSV map.

For: Controls engineers reviewing an offline serial capture with a device register map. A CRC-valid byte sequence still needs explicit address context, byte order, scale and coverage evidence.

## Quickstart

Python 3.10 or newer; no runtime packages or network access. The wheel build needs setuptools from the normal Python package registry.

```sh
git clone https://github.com/nripankadas07/modbus-frame-ledger.git
cd modbus-frame-ledger
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/modbus-frame-ledger example.hex example.csv --start 0
```

Exit 0, with temperature -10, status 0 and pressure 12.5. All four captured registers are covered.

Windows equivalents use `.venv\Scripts\python.exe` and `.venv\Scripts\modbus-frame-ledger.exe`; Windows/macOS are not executed by this release’s Linux CI.

## Contract

ASCII hexadecimal RTU response, expected unit 1–247 and function 3 or 4, and mandatory zero-based --start supplied from the request. The response does not carry its start address: context is caller asserted. Validate length, even byte count and CRC16/MODBUS; CRC is not authentication. CSV columns exactly name,address,type,order,scale,offset. u16/i16 use AB or BA; u32/i32/f32 use ABCD/BADC/CDAB/DCBA. Byte-order labels describe wire order relative to canonical ABCD. Scale and offset use exact decimal arithmetic; finite binary32 values retain their exact binary value before scaling.

JSON goes to stdout. Exit 0 means a valid report without findings; exit 1 means a valid report with the documented findings; exit 2 means invalid input or an I/O failure, with an error on stderr and no partial report. `--help` describes options. Review outputs before sharing them; they may contain input identifiers.

## Limits

One frame of 5–256 bytes and at most 125 registers; CSV 64 KiB and 125 rows. No overlapping mapped spans, serial ports, TCP, polling, device writes, request capture pairing, authentication or device-specific register semantics. Exceptions, unmapped words, map rows outside the response and nonfinite floats produce valid exit-1 evidence. Exact numeric representation is not a claim about sensor measurement precision.

## Verify

```sh
python3 -m unittest -v test_behavior
python3 -m compileall -q .
python3 -m pip wheel --no-deps --wheel-dir dist .
python3 -m venv /tmp/modbus-frame-ledger-check
/tmp/modbus-frame-ledger-check/bin/python -m pip install --no-deps dist/*.whl
python3 verify_installed.py /tmp/modbus-frame-ledger-check/bin/python
```

Installed-command checks run outside the checkout. See [validation](VALIDATION.md), [research](RESEARCH.md), [contributing](CONTRIBUTING.md), [support](SUPPORT.md) and [security](SECURITY.md).

Original implementation and invented fixtures developed with AI assistance. MIT license. No production adoption, competitor feature-absence or performance-superiority claim.
