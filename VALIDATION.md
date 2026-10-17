# Validation

Acceptance: Verify known CRC vectors, all byte orders, signed values, binary32 scaling, complete map coverage, CRC failure and valid exception/nonfinite/out-of-range findings.

The behavior suite has 18 test methods, including malformed-input contracts. CI runs unit tests, compilation, wheel build and new-environment installed-command checks on Linux/Python 3.10, 3.12 and 3.14. A configured workflow does not prove success; inspect current Actions results. Preparation receipts are recorded in PREPARATION.json after execution. All possible inputs, production workloads and Windows/macOS are not certified. No performance benchmark was conducted.
