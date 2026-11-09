# LOOM–PUNO reactive field — independent local QA receipt

**Date:** 2026-11-09 (UTC)  
**Scope:** Local code inspection and machine execution of code embedded in the collaborator's pasted message. No external access, deployment, Sphere integration, VPS modification, or architecture promotion. The collaborator's original code was extracted verbatim into a separate local file and not modified.

**Source file:** `loom_puno_field_original.py`  
**SHA-256 (extracted Python):** `34a2e7c561a70f85c075f9c88d5f795ba6141728a3ede96db9b3d7ac6ba5de65`  
**Source size:** 14130 UTF-8 bytes  
**Source Python lines:** 303  
**Python used:** 3.13.5  
**Independent QA:** `loom_puno_independent_qa.py`.

## Aggregate outcome

**NOT YET FUNCTIONING for the central KIP admission path.** Six of twelve independently defined checks met expected behaviour. These are not the collaborator's promised eleven tests: that suite was not included in the submitted artifact.

| Probe | Outcome | Evidence |
|---|---|---|
| Q01 Valid Python syntax | PASS | Python AST parses |
| Q02 Included eleven-test suite | ABSENT | No test functions or main runner; invoking the `.py` file exits without test output |
| Q03 Wake roots | PASS | 2 participant roots, 3 trace events |
| Q04 First human text arrival to KIP | FAIL | `KeyError: 'provenance'` |
| Q05 Unrecognised form to KIP | FAIL | `KeyError: 'provenance'` |
| Q06 Direct arrival to L | PASS | Recipient L accepts event |
| Q07 L-only arrival replay | PASS | Reconstructed trace matches original |
| Q08 Missing dialect detection | PASS | `FieldIntegrityError` raised |
| Q09 Tamper detection on a recorded L event | PASS | `FieldIntegrityError` raised |
| Q10 Live trace immutability | FAIL | Resident can mutate the shared trace through the `tail` argument without refusal |
| Q11 Auditing of in-place state mutation | FAIL | Resident can alter its owned state without a transformation event being recorded |
| Q12 KIP UNKNOWN branch, after supplying expected provenance for this probe | FAIL | `UnboundLocalError` for `new_own_fa` |

## Actionable findings, without claiming a fix

1. **Packet schema inconsistency:** `Field.admit` creates `{'content', 'source', 'form_tag'}`, while `kip_respond` expects `packet['provenance']['source']`. The KIP response fails on the first ordinary input. Agree on one source/provenance contract and test both known and UNKNOWN forms.
2. **Undefined fallback variable:** `new_own_fa` is used after both branches but is not assigned in the UNKNOWN branch. Test with an unrecognised `form_tag` after resolving the packet mismatch.
3. **Missing validation suite:** The source has no test runner and no tests, despite the text announcing eleven tests. Include the committed tests and expected trace independently from post hoc corrections.
4. **Mutable trace exposure:** `_visible_tail` passes a shallow copy of the trace list whose event dictionaries are still live mutable objects. A resident function can overwrite earlier events, contradicting L5. Test with a deliberately mutating resident.
5. **Shared state aliasing:** `_owned_states` returns state dictionaries by reference. A resident mutating those dictionaries in place can bypass the comparison that would otherwise emit a `transformation` event; this is an L5/L8 integrity exposure. Test copy isolation and replay semantics.
6. **End-to-end radiator scenario and persistence claim remain BLOCKED** by the immediate KIP failure; only the direct-to-L replay pathway has been machine-verified.

## Engineering and epistemic boundary

This receipt tests the **submitted implementation**, not universal PUNO. It neither proves nor disproves native KIP, lawful possibility, materiality, consciousness, origination, or the observer-relative 5D analogy. The positive L-route checks do not rescue the blocked KIP path. The collaborator's hand-trace prediction remains **unverified and inconsistent with current executable behaviour**; keep it unchanged as a prediction for comparison.

**Reproduce:** `python loom_puno_independent_qa.py` with the original extracted Python in the same directory.

**Result:** `IMPLEMENTATION_CORRECTIONS_REQUIRED / NO_FUNCTIONAL_PROMOTION / NO_EXTERNAL_WRITES`.
