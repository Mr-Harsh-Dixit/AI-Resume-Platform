# S0-03 builder evidence - rule taxonomy

## Scope

- Step: `S0-03 - Create the rule taxonomy`
- Builder: Codex lead implementation agent
- Initial evidence date: 2026-08-03
- Remediation evidence date: 2026-08-04
- Candidate taxonomy: `rulebook/taxonomy/1.0.0/taxonomy.json`
- Schema: `rulebook/schemas/rule-taxonomy.schema.json`
- Semantic lock: `rulebook/taxonomy/1.0.0/semantic-lock.json`
- Controlled locator index: `rulebook/sources/1.0.0/source-locator-index.json`

S0-03 defines classification semantics only. Production rule IDs and complete handbook classification remain in S0-04; authority precedence remains in S0-05.

## Source traceability

- Handbook v1.0 pages 2, 7, 21, and 27-29: scope and examples, constraint concepts, hard/strong/situational distinctions, truth/privacy, hard gates, and diagnostic scoring.
- Specification v1.3 pages 16 and 19-21: platform rule categories and required six-class Stage 0 taxonomy.
- Source baseline: `S0-SOURCE-BASELINE-001`.
- Rendered specification boundary: page 20 ends with `Deliverables`; `Precautions` begins on page 21.

The taxonomy paraphrases operational behavior and does not reproduce long handbook passages or copy illustrative candidate facts.

## Implemented invariants

- Exactly one primary class from the approved six-class set.
- Hard failures block and cannot be offset by scoring.
- Strong-default exceptions require authority, reason, context, and a regression test.
- Situational rules require bound context and forbid silent generic fallback.
- Examples are non-executable and forbidden as candidate content.
- Explanatory guidance is non-executable.
- Ambiguous classification fails closed for human review.
- A pinned Draft 2020-12 engine applies the complete JSON Schema in tests and CI.
- Prompt reclassification is prohibited by schema, a structured AI-authority policy, and invariant `TAX-INV-009`.
- Canonical SHA-256 fingerprints reject same-version semantic or locator-index drift.
- Taxonomy references bind to frozen source checksums and controlled section/page locators.
- Unknown fields, private workstation paths, out-of-range locators, source drift, and silent reclassification are rejected.

## Automated evidence

Commands run from the repository root:

```text
python -m pip install -r requirements/verification.txt
python -m unittest discover -s tests -v
python tools/verify_stage0_control_plane.py
python tools/verify_rule_taxonomy.py
git diff --check
```

Remediation-cycle 1 result before publication:

- Unit tests: PASS - 34 tests.
- Stage 0 control-plane verification: PASS.
- Rule-taxonomy schema, semantic-lock, and source-binding verification: PASS.
- Reviewer mutation replay: PASS - all seven previously accepted invalid cases now rejected.
- Whitespace/error-marker check: PASS.

Negative tests cover the original cases plus every mutation demonstrated by the independent FAIL: schema-invalid override values, duplicate prohibited uses, prompt-safeguard removal, missing AI policy, same-version semantic reclassification, out-of-range pages, unknown controlled sections, checksum drift, and locator-index drift.

## Review and remediation history

- Reviewed commit: `8f90f2a474bad9f95e47f33655f3847fc0e7694d`.
- Product/domain verdict: `PASS`.
- Technical and overall verdict: `FAIL`.
- Retained review evidence: `docs/stage-0/evidence/S0-03-REVIEW-FAIL-2026-08-03.md`.
- Reproduction: all seven demonstrated invalid mutations were accepted before remediation.
- Remediation cycle: 1, builder checks complete, fresh independent review required.

Fresh review of commit `3855d434d3d97639c5b066e02e9951e105060495` retained the product/domain PASS and returned technical `FAIL` because `Stage 0 precautions` was mapped to rendered page 20 rather than page 21. Evidence is retained in `docs/stage-0/evidence/S0-03-REVIEW-FAIL-2026-08-04.md`.

Remediation cycle 2:

- Corrected the controlled locator to page 21.
- Refreshed the source-locator SHA-256 in the semantic lock to `1a491281fcae6a55b5f1be28816a99524ebb10f6cbb94519082f0cb58b01a3cc`.
- Added an exact test requiring `Stage 0 precautions` to equal `[21]`.
- Unit tests: PASS - 35 tests, including the exact locator regression.
- Stage 0 control-plane verification: PASS.
- Rule-taxonomy schema, semantic-lock, and source-binding verification: PASS.
- Whitespace/error-marker check: PASS.
- Builder evidence is ready; another fresh independent review is still required.

## Review and completion state

- Builder state: `evidence_ready`.
- Product/domain review: `PASS` on the failed revision; product-owner completion approval remains required.
- Independent technical verdict: two retained `FAIL` verdicts; another fresh verdict is required after cycle 2.
- Published implementation commit: `3c0717f888c16e4372260f1072b557697a581062`.
- Draft remediation pull request: <https://github.com/Mr-Harsh-Dixit/AI-Resume-Platform/pull/5>.
- GitHub Actions on the published implementation: `PASS`, run <https://github.com/Mr-Harsh-Dixit/AI-Resume-Platform/actions/runs/30843704738>.
- PR #5 remains unmerged. S0-03 must not become `passed` until the exact remediated revision receives a fresh PASS and its GitHub checkpoint is recorded.

## Known limitations and residual risk

- The taxonomy is a candidate and contains no production rule records yet.
- Source classification still requires human domain judgment during S0-04.
- The taxonomy prevents scoring from overriding hard rules but does not define full cross-rule authority precedence; S0-05 owns that contract.
- The semantic lock makes changes review-visible; it does not authorize a changed lock. This correction is to an unapproved candidate and requires fresh review. After acceptance, any semantic or locator update requires a new version and fresh review.
- The controlled locator index covers only the source sections used by S0-03. S0-04 must add versioned, reviewed locators for production rule records.
