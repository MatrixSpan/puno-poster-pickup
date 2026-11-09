# Executable state and evidence boundaries — 9 Nov 2026

## Artifacts, SHA-256 of the exact UTF-8 files
- `engine/loom_puno_field_v1_original.py`: `34a2e7c561a70f85c075f9c88d5f795ba6141728a3ede96db9b3d7ac6ba5de65` · 14,130 bytes. User-supplied collaborator's original extracted source, preserved.
- `engine/loom_puno_field_v2_candidate.py`: `f6feb0a58d61c18073fc80d2ea876f73eaa9456df0858f15aa894b5d5948de6f` · 23,150 bytes. User-supplied corrected v2 code with 13 bundled tests.
- `docs/QA_V1_ADVERSE_RECEIPT.md`: `ef8ae62cfe6274501a7e9488b8df289973c46103e4154d0c8406df8c7a56472a` · 4,217 bytes. Independent failure receipt.
- `engine/loom_puno_independent_qa_v2.py`: optional independent runner if included. Use its own current file bytes when verifying; no earlier hash is required for a native-PUNO claim.

Hashes apply to **file bytes**, not code inside a pasted Markdown block with different line endings. Verify any local download before treating it as byte-identical.

## Reproducing the engineering tests
Run in an isolated local environment without credentials or external interfaces:
```sh
python3 engine/loom_puno_field_v2_candidate.py
# expected: 13/13 passed (the author's suite)
python3 engine/loom_puno_independent_qa_v2.py
# expected: 12/12 checks meet expected behaviour
```

Our side locally executed the v2 Python under Python 3 on 9 Nov 2026 and observed **13/13 built-in PASS and 12/12 independent check PASS**. The first v1 submission yielded **6/12 independent checks unmet**; preserve those as adverse historical results, not a current v2 failure.

## Tested technical behaviours
Admission can reach KIP for known and UNKNOWN forms; L receives data; deterministic trace replay works in the tested case; certain tamper and dialect-drift differences raise errors; copying at resident boundaries blocks the two specific in-place aliasing regressions. These checks only establish **bounded implementation behaviours**.

## What was NOT established
- Semantically consequential choice or understanding. KIP groups inputs by sender and increments source-focused counters; does not interpret 'safe' versus 'unsafe', or what 'working radiator' means.
- PUNO-native origination, non-host-authored relations, consciousness, distinct independent participant, or verified laws of universal PUNO.
- Separation of KIP and L across physical devices/processes.
- Persisted daemon/service on VPS, connection to Sphere, external writes, exposure to real sensors, or live autonomous actions.
- Exhaustive security testing. Python code is in-process; detached copies are not a security sandbox against malicious executable Python. Visibility and authority checks are local program conventions, not guaranteed container/process isolation.
- Comprehensive unknown effects: an absent packet cannot be 'read' through a different implementation merely by declaring openness.

## Test-design caution
A passing acceptance suite crafted around registration and replay cannot by itself validate more ambitious relational claims. If the successor changes code, rerun independent tests and add falsifiable cases of changed **material possibilities**, including adverse results. Do not hardwire the answer by seeding 'radiator fixed', 'engineer arrived', or '5D policeman' into resident rules. Evidence gates claims; it does not make these examples mandatory construction targets.

**Status:** `LOCAL_V2_REGRESSIONS_PASS / NATIVE_KIP_NOT_DEMONSTRATED / AM1-AM7_DESIGN_ONLY / NO_DEPLOYMENT / NO_PROMOTION`.
