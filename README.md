# AI Resume Platform

This repository is the controlled implementation workspace for the AI Resume Platform specified in **AI Resume Platform - Staged Development Specification v1.3** and governed by **The Professional Resume Handbook: ATS-Safe, Evidence-Driven, Job-Targeted Resumes v1.0**.

## Current delivery state

- Stage: `S0 - Product, rights and rulebook baseline`
- State: `BLOCKED_ENTRY_CONDITIONS`
- Application code: intentionally not started
- Active package: S0-03 rule-taxonomy remediation and fresh review
- GitHub remote: public `Mr-Harsh-Dixit/AI-Resume-Platform`

The specification requires Stage 0 to close before Stage 1 design and before application code depends on resume rules. Preparatory artifacts may be built while an entry condition is unresolved, but they cannot be reported as passed.

## Source-of-truth order

1. Product-owner decisions recorded in the decision log.
2. AI Resume Platform Staged Development Specification v1.3.
3. Versioned rule, occupation-profile, template, and output-contract packages approved under Stage 0.
4. Professional Resume Handbook v1.0 as the attributed domain source.
5. Implementation code, prompts, and renderer behavior.

Lower-priority artifacts may not silently override a higher-priority source. Handbook examples are never candidate facts.

## Delivery controls

- A step is complete only after its deliverables and checks pass, independent review returns `PASS`, remediation is closed, and the exact reviewed revision is pushed to GitHub.
- A stage is complete only after every exit criterion has retained evidence, independent review returns `PASS`, and the stage checkpoint is published to GitHub.
- `FAIL` returns work to the accountable builder. `BLOCKED` remains visibly incomplete.
- Beta and production releases additionally require an explicit product-owner gate decision.

See [delivery workflow](docs/governance/DELIVERY_WORKFLOW.md), [Stage 0 status](docs/stage-0/STATUS.json), and [Stage 0 traceability](docs/stage-0/TRACEABILITY.md).

## Local verification

Install the pinned verification dependency and run the checks from the repository root:

```powershell
python -m pip install -r requirements/verification.txt
python -m unittest discover -s tests -v
python tools/verify_stage0_control_plane.py
python tools/verify_rule_taxonomy.py
```

These checks apply Draft 2020-12 JSON Schema validation, enforce status integrity and source bindings, reject same-version taxonomy drift, and prevent any step or stage from passing without review and GitHub evidence.
