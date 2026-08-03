# Stage 0 decision log

This log records product-owner decisions and unresolved interpretation or governance questions. `Proposed` and `Pending` entries are not authorization to implement dependent behavior.

| ID | Decision | Owner | State | Current position / required response | Affected work |
|---|---|---|---|---|---|
| DEC-S0-001 | Handbook ownership and commercial operationalization rights | Product owner / rights authority | **Passed** | The product owner confirmed authorship and commercial rule operationalization permission on 2026-08-03, then verified continuation after the GitHub checkpoint. The public repository contains derived rules and traceability, not the source PDF. | S0-01, S0-EXIT-01, commercial launch |
| DEC-S0-002 | GitHub repository and visibility | Product owner | **Accepted** | Create public repository `Mr-Harsh-Dixit/AI-Resume-Platform`. Source documents and private data remain excluded. | Every step/stage checkpoint |
| DEC-S0-003 | Named review authorities | Product owner | **Partially accepted** | Non-builder Codex reviews returned technical FAIL on commits `8f90f2a474bad9f95e47f33655f3847fc0e7694d` and `3855d434d3d97639c5b066e02e9951e105060495`; the second isolated an incorrect Stage 0 precautions page locator. Product/domain PASS remains valid. The implementing Codex remains accountable for remediation and cannot issue the fresh PASS. Product-owner approval and named qualified reviewers for later occupation-profile gates remain required. | Stage entry, S0-03, S0-06, S0-07, S0-EXIT-04, S0-EXIT-08 |
| DEC-S0-004 | Launch market and launch profiles | Product owner + field reviewers | **Pending** | Recommended baseline is English private-sector A4/Letter with Standard Professional/Technology plus one market-specific Maritime/Merchant Navy package. State market/country and approve or replace this set. | S0-07, S0-08, S0-09, fixtures |
| DEC-S0-005 | Product boundary from specification v1.3 | Product owner | **Acceptance pending** | General and Job-Targeted are separate modes; occupation profile, template, and output format are separate choices; outputs are DOCX, PDF, and LaTeX; commercial target is USD 2-5. Provision of the approved specification is evidence, but the gate still requires an explicit owner acceptance record. | S0-ENTRY-02, S0-EXIT-03 |
| DEC-S0-006 | Controlled source storage | Product owner + lead developer | **Passed** | The product owner approved the private repository boundary, immutable commit-pinned URLs, checksums, and versioned replacement policy on 2026-08-03 by directing merge of the reviewed S0-02 candidate. The source files remain excluded from the public implementation repository. | S0-02 |
| DEC-S0-007 | Application technology stack | Lead developer + product owner | **Proposed** | Proposed: Next.js/TypeScript, FastAPI/Python, Supabase, OpenAI Responses API, and isolated document workers. Treat model names, provider capabilities, versions, pricing, and hosting assumptions as configuration requiring live verification before Stage 2 closure. | Architecture decision before Stage 2 |
| DEC-S0-008 | Step/stage GitHub publication rule | Product owner | **Accepted** | A step or stage is not complete until the exact reviewed revision and evidence are pushed to GitHub. | All delivery governance |

## Decision record template

Append a dated record rather than rewriting history:

```text
Decision ID:
Decision date:
Decision owner and authority:
Decision:
Rationale:
Alternatives rejected:
Affected rule/step IDs:
Evidence link:
Review/expiry date:
```
