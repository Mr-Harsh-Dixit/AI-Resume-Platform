# Repository execution rules

These rules apply to every human or automated contributor in this repository.

## Authority and sequencing

- Read `docs/stage-0/STATUS.json`, `docs/stage-0/TRACEABILITY.md`, and the current decision log before changing scoped work.
- Treat the staged specification and handbook versions recorded in `docs/stage-0/SOURCE_BASELINE.json` as authoritative inputs.
- Do not begin application implementation while Stage 0 is open. Do not begin a later stage until its declared dependencies have passed.
- Do not treat the proposed TypeScript/Python/Supabase/OpenAI stack as approved until its decision record is accepted.

## Completion and GitHub

- Never self-certify implementation work. The builder supplies evidence; an independent reviewer returns `PASS`, `FAIL`, or `BLOCKED`.
- Never mark a step `passed` without automated/manual evidence, a reviewer verdict, an immutable commit SHA, and a GitHub URL for the reviewed revision.
- Never mark a stage `passed` without every exit criterion passing and a published stage checkpoint.
- Use one focused branch or pull request per numbered implementation step. Preserve remediation and fresh-review history.
- Do not stage, rewrite, or discard unrelated user changes.

## Safety and integrity

- Truth, privacy, explicit vacancy instructions, eligibility, market rules, parsing/readability, and aesthetics are enforced in that precedence order.
- AI output is provisional structured data. Deterministic validation and candidate approval control release.
- Never invent candidate facts, credentials, metrics, eligibility, employers, titles, tools, or responsibilities.
- Never execute user-supplied templates, macros, active content, external resources, or LaTeX.
- Do not place resume text, source documents, absolute workstation paths, secrets, tokens, or personal data in ordinary logs or public artifacts.
- Unsupported occupations, markets, formats, and claims must fail visibly; no silent generic fallback is allowed.
