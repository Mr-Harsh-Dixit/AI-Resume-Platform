# Stage 0 traceability matrix

Source: AI Resume Platform Staged Development Specification v1.3, pages 19-21.

Status values follow the [delivery workflow](../governance/DELIVERY_WORKFLOW.md). Preparatory work may reach `evidence_ready` while the stage entry gate remains blocked; only independent review plus a GitHub checkpoint can produce `passed`.

## Entry conditions

| ID | Condition | Current state | Evidence or blocker |
|---|---|---|---|
| S0-ENTRY-01 | Handbook file and version identified | `evidence_ready` | `SOURCE_BASELINE.json` |
| S0-ENTRY-02 | Price band, two modes, field profiles, and LaTeX requirement stated | `evidence_ready` | Approved specification v1.3 |
| S0-ENTRY-03 | Owners assigned for scope, rights, rule interpretation, and every launch profile | `blocked` | DEC-S0-003 and DEC-S0-004 |

## Detailed steps

| ID | Specification step | Required output | Current state | Dependency or next proof |
|---|---|---|---|---|
| S0-01 | Confirm commercial usage rights | Owner/rights statement and permitted uses | `passed` | DEC-S0-001, product-owner review evidence, PR #1 checkpoint |
| S0-02 | Freeze the baseline | Immutable source manifest, checksum, storage URI, change policy | `passed` | Product-owner PASS in `evidence/S0-02-REVIEW.md` and PR #4 checkpoint |
| S0-03 | Create rule taxonomy | Versioned classes: hard, strong default, situational, scoring, example, explanatory | `evidence_ready` | Product/domain PASS retained; technical FAIL under remediation; fresh independent review required |
| S0-04 | Assign rule IDs | Stable IDs, source page/section, rationale, test condition | `not_started` | S0-03 |
| S0-05 | Define precedence | Machine-testable truth/privacy-to-aesthetics ordering | `not_started` | S0-03 |
| S0-06 | Define occupation-profile contract | Versioned schema and review fields | `not_started` | Reviewer ownership |
| S0-07 | Select launch profiles | Bounded approved launch set and review evidence | `blocked` | DEC-S0-003 and DEC-S0-004 |
| S0-08 | Define sensitive-field policy | Purpose, consent, display, retention, and prohibited scopes | `not_started` | S0-06 and S0-07 |
| S0-09 | Define supported markets | Approved English private-sector scopes and explicit unsupported results | `blocked` | DEC-S0-004 |
| S0-10 | Define canonical output contract | Typed ResumeDocument and DOCX/PDF/LaTeX equivalence contract | `not_started` | None beyond Stage 0 controls |
| S0-11 | Define template governance | Compatibility, recommendation, private upload, rights, moderation, deletion, publication | `not_started` | None beyond Stage 0 controls |
| S0-12 | Define product claims | Approved promise and prohibited marketing | `not_started` | Product-owner approval |
| S0-13 | Create fictional fixtures | Career-stage, gap, confidentiality, eligibility, technology, maritime, and leakage cases | `not_started` | Rule/profile/output contracts |
| S0-14 | Create decision log | Ambiguity, owner, decision, date, affected IDs | `in_progress` | Owner responses and ongoing maintenance |

## Deliverable coverage

| Deliverable | Producing steps | State |
|---|---|---|
| Product scope and exclusions | S0-07, S0-09, S0-12 | `not_started` |
| Machine-readable rule catalog with sources | S0-03, S0-04, S0-05 | `not_started` |
| Occupation-profile schema and approved packages | S0-06, S0-07, S0-08 | `blocked` |
| Template-governance contract and library policy | S0-11 | `not_started` |
| ResumeDocument and multi-format output contract | S0-10 | `not_started` |
| Product promise and prohibited marketing | S0-12 | `not_started` |
| Evaluation fixtures and decision log | S0-13, S0-14 | `in_progress` |

## Exit criteria

| ID | Exit criterion | Current state | Required evidence |
|---|---|---|---|
| S0-EXIT-01 | Commercial rights confirmed or owner resolves risk | `passed` | `evidence/S0-01-REVIEW.md` and PR #1 |
| S0-EXIT-02 | Every MVP hard rule has ID, source, and test | `not_started` | Catalog validation plus rule tests |
| S0-EXIT-03 | General and Targeted boundaries approved | `in_review` | Product-owner acceptance of specification boundary |
| S0-EXIT-04 | Every launch profile is sourced, reviewed, field-complete, and fixture-covered | `blocked` | Profile packages and qualified reviewer verdicts |
| S0-EXIT-05 | DOCX/PDF/LaTeX content equivalence is defined | `not_started` | Schema, renderer invariants, and contract tests |
| S0-EXIT-06 | Template lifecycle and rights controls are approved/testable | `not_started` | Contract, schemas, security cases, review verdict |
| S0-EXIT-07 | Unsupported boundaries are visible | `not_started` | Scope contract and unsupported fixtures |
| S0-EXIT-08 | Independent source trace is unambiguous | `blocked` | Rule sample and independent traceability verdict |

## Hard stop

Stage 1 design and all application implementation remain dependency-blocked until every Stage 0 exit criterion is supported by evidence and independently passed. A GitHub push without that review is a work checkpoint, not stage completion.
