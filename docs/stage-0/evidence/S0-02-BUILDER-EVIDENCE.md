# S0-02 builder evidence - frozen source baseline

## Scope

- Step: `S0-02 - Freeze the source baseline`
- Builder: Codex lead implementation agent
- Evidence date: 2026-08-03
- Public baseline ID: `S0-SOURCE-BASELINE-001`
- Private source repository: `Mr-Harsh-Dixit/AI-Resume-Platform-Sources`
- Pinned private commit: `96986c06e6b6f0b7e3105bb88fe41e41b74ab5b3`

## Storage controls

- GitHub reports the source repository visibility as `PRIVATE`.
- Both source links are pinned to the exact 40-character commit ID, not `main` or another mutable ref.
- Version-specific paths are immutable; a source change requires a new semantic-version directory and public baseline ID.
- The public implementation repository retains filenames, concise metadata, checksums and private access-controlled URLs, but not the source file bytes.
- The private manifest prohibits unapproved public copying and replacement of an existing version path.

## Integrity evidence

| Source | Size | SHA-256 | Private Git blob |
|---|---:|---|---|
| `HANDBOOK-1.0` | 182,673 bytes | `05927b5fb2f4dc4ff44e7026a751c84e97ce5332f88d1fe48eda07ec19839fd8` | `ab38cdb363bccb06795d267224768800664a7129` |
| `SPEC-1.3` | 94,148 bytes | `4afd26ce2d57362d8ab3e5fc334ee20a896dda5db844420fdf50ff8606e75b35` | `008009919df4e9330b2cd26d8a513408470de10d` |

The copied files were rehashed after transfer and matched the hashes recorded from the originals. GitHub's contents API confirmed the expected paths and sizes at the pinned commit.

## Automated evidence

Private repository command:

```text
python verify_sources.py
```

Result: `PASS - Private authoritative sources match the immutable manifest.`

Private GitHub Actions workflow:

- Workflow: `Verify authoritative sources`
- Run: <https://github.com/Mr-Harsh-Dixit/AI-Resume-Platform-Sources/actions/runs/30835424708>
- Head commit: `96986c06e6b6f0b7e3105bb88fe41e41b74ab5b3`
- Result: `SUCCESS`

The public control-plane tests additionally reject missing storage URIs, mutable source URLs, unapproved repository copying and source-manifest drift.

## Review and completion state

- Builder state: `evidence_ready`.
- Product-owner review: pending for repository visibility, pinned locations and source identity.
- GitHub S0-02 completion checkpoint: pending dedicated pull request.
- S0-02 must not become `passed` until the product-owner review verdict and exact public checkpoint are recorded.

## Residual risk

- Repository privacy depends on GitHub account and collaborator security; access changes must be audited.
- A private GitHub repository is the MVP governance store, not candidate-data storage.
- Future production source packages may move to separately managed private object storage, but any migration must preserve pinned hashes, access control and audit evidence.
