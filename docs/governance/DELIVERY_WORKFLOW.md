# Delivery workflow and GitHub checkpoints

## Purpose

This workflow operationalizes the specification's builder-reviewer loop and the product owner's requirement that GitHub be updated when every step and stage completes.

## State model

| State | Meaning |
|---|---|
| `not_started` | No implementation evidence exists. |
| `in_progress` | The builder is working; the item is incomplete. |
| `evidence_ready` | Builder checks pass and evidence is assembled; independent review is still required. |
| `in_review` | An independent reviewer is evaluating the exact candidate revision. |
| `blocked` | A named dependency or owner decision prevents progress or review. |
| `failed` | Independent review found one or more unmet criteria. |
| `passed` | Review returned `PASS` and the exact reviewed revision is published to GitHub. |

`evidence_ready` is not completion. A local commit, build success, numeric score, or builder statement is never equivalent to `passed`.

## Per-step lifecycle

1. Create a focused branch named `agent/s<stage>-step-<nn>-<slug>`.
2. Implement only that numbered specification step and its directly required controls.
3. Run the declared automated checks and retain relevant manual evidence.
4. Record limitations, risks, owners, and due dates.
5. Push the candidate revision and open or update its pull request as a reviewable checkpoint.
6. An independent reviewer returns `PASS`, `FAIL`, or `BLOCKED` against explicit criteria.
7. On `FAIL`, the same accountable builder remediates on the same workstream; a fresh review evaluates the new revision and regression risk.
8. On `PASS`, record reviewer identity, verdict date, exact commit SHA, pull-request URL, and evidence paths in `STATUS.json`.
9. Merge only the reviewed revision according to repository protection rules. The pushed reviewed SHA is the completion checkpoint required by the product owner.

## Per-stage lifecycle

1. Confirm every stage step and exit criterion is traceable to retained evidence.
2. Pin the exact code, rule packages, schemas, prompts/models, templates, compilers, and dependencies reviewed, as applicable.
3. Obtain an independent stage verdict. Technical `PASS` does not authorize beta or production.
4. Publish a stage-closure pull request that updates the status file, evidence index, risks, remediation history, and next-stage dependency state.
5. Record the merged commit and GitHub URL as the immutable stage checkpoint.
6. Obtain an explicit product-owner decision for beta or production gates.

## Required evidence fields

Every `passed` step or stage must identify:

- exact acceptance criteria;
- automated test command and result;
- relevant manual review evidence;
- known limitations and residual risks;
- independent reviewer, verdict, and date;
- remediation history or an explicit statement that none was required;
- reviewed commit SHA and GitHub URL.

## Defensive publication rules

- Do not publish source documents unless ownership, repository visibility, and reuse rights explicitly permit it.
- Source manifests contain stable filenames and checksums, not workstation paths.
- Do not push secrets, candidate data, raw AI prompts containing personal data, generated private resumes, or unmoderated template uploads.
- If GitHub is unavailable, retain work as incomplete and report the publishing blocker. Do not substitute a local commit for the required checkpoint.
