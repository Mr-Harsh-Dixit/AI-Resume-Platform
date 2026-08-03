# S0-03 builder evidence - rule taxonomy

## Scope

- Step: `S0-03 - Create the rule taxonomy`
- Builder: Codex lead implementation agent
- Evidence date: 2026-08-03
- Candidate taxonomy: `rulebook/taxonomy/1.0.0/taxonomy.json`
- Schema: `rulebook/schemas/rule-taxonomy.schema.json`

S0-03 defines classification semantics only. Production rule IDs and complete handbook classification remain in S0-04; authority precedence remains in S0-05.

## Source traceability

- Handbook v1.0 pages 2, 7, 21, and 27-29: scope and examples, constraint concepts, hard/strong/situational distinctions, truth/privacy, hard gates, and diagnostic scoring.
- Specification v1.3 pages 16 and 19-21: platform rule categories and required six-class Stage 0 taxonomy.
- Source baseline: `S0-SOURCE-BASELINE-001`.

The taxonomy paraphrases operational behavior and does not reproduce long handbook passages or copy illustrative candidate facts.

## Implemented invariants

- Exactly one primary class from the approved six-class set.
- Hard failures block and cannot be offset by scoring.
- Strong-default exceptions require authority, reason, context, and a regression test.
- Situational rules require bound context and forbid silent generic fallback.
- Examples are non-executable and forbidden as candidate content.
- Explanatory guidance is non-executable.
- Ambiguous classification fails closed for human review.
- Unknown fields, private workstation paths, source drift, and silent reclassification are rejected.

## Automated evidence

Commands run from the repository root:

```text
python -m unittest discover -s tests -v
python tools/verify_stage0_control_plane.py
python tools/verify_rule_taxonomy.py
git diff --check
```

Builder result before publication:

- Unit tests: PASS - 19 tests.
- Stage 0 control-plane verification: PASS.
- Rule-taxonomy semantic verification: PASS.
- Whitespace/error-marker check: PASS.

Negative tests cover class duplication, hard-rule exceptions, score compensation, incomplete strong-default exception evidence, situational fallback, example reuse, ambiguous classification, unknown sources, unknown fields, and duplicate context axes.

## Review and completion state

- Builder state: `evidence_ready`.
- Product/domain review: pending.
- Independent technical verdict: pending.
- GitHub Actions result: pending branch publication.
- S0-03 must not become `passed` until the exact reviewed revision, verdict, remediation history, and GitHub checkpoint are recorded.

## Known limitations and residual risk

- The taxonomy is a candidate and contains no production rule records yet.
- Source classification still requires human domain judgment during S0-04.
- The taxonomy prevents scoring from overriding hard rules but does not define full cross-rule authority precedence; S0-05 owns that contract.
- The dependency-free validator enforces the security-critical subset of the JSON Schema. A production schema toolchain will be selected and pinned during architecture implementation.
