# Stage 0 rule taxonomy

## Outcome

The machine-readable taxonomy at `rulebook/taxonomy/1.0.0/taxonomy.json` defines exactly six primary classes:

1. `hard` - blocks the affected claim, generation, export, or valid submission state.
2. `strong_default` - applies unless a documented higher-authority context justifies a tested exception.
3. `situational` - selects behavior only from explicitly bound and approved context.
4. `scoring` - contributes a bounded diagnostic and never compensates for a hard failure.
5. `example` - illustrative only and forbidden as candidate content or evidence.
6. `explanatory` - background or rationale that is not executable product logic.

Every source statement receives exactly one primary class. Secondary topics such as truth, privacy, ATS, targeting, formatting, occupation, or document QA will be added during S0-04 without altering primary enforcement semantics.

## Classification procedure

Classify the source statement itself, not the topic it describes:

1. If it is fictional or illustrative, classify it as `example`, even when it demonstrates a hard-rule violation.
2. If it only provides background or rationale, classify it as `explanatory`.
3. If violation must block a claim or release path, classify it as `hard`.
4. If it only adds a bounded diagnostic result, classify it as `scoring`.
5. If correct behavior changes with an approved context axis, classify it as `situational`.
6. If it is normally applied but has a documented and tested exception path, classify it as `strong_default`.
7. If none is unambiguous, return `reject_until_human_review`.

This ordering prevents illustrative text from accidentally becoming executable logic and prevents ambiguous guidance from being forced into a permissive class.

## Enforcement boundaries

- Prompts and model output cannot change a rule's class.
- A numeric readiness result cannot override a hard failure.
- Strong-default exceptions require an authority, reason, bound context, and regression test.
- Situational rules cannot run without context and cannot silently fall back to generic behavior.
- Examples never populate candidate evidence, metrics, titles, credentials, claims, or generated wording.
- Explanatory guidance requires a new versioned rule record and review before it can become enforceable.

## Deliberate exclusions

S0-03 does not:

- assign production rule IDs or topic namespaces - S0-04;
- define cross-rule authority precedence - S0-05;
- approve occupation-profile behavior - S0-06 through S0-09;
- define the ResumeDocument schema - S0-10; or
- classify every handbook statement - S0-04.

## Source map

- Handbook v1.0 pages 2, 7, 21, and 27-29: scope, examples, rule distinctions, truth/privacy, hard gates, and diagnostic scoring.
- Specification v1.3 pages 16 and 19-21: platform rule categories and required Stage 0 taxonomy behavior.

## Review state

Status: `evidence_ready`. Automated structural and semantic-invariant checks are required before review. The taxonomy remains `candidate` until a non-builder technical reviewer and the product owner approve it.
