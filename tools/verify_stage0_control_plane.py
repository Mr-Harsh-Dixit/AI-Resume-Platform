"""Dependency-free integrity checks for the Stage 0 control plane."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "docs" / "stage-0" / "STATUS.json"
BASELINE_PATH = ROOT / "docs" / "stage-0" / "SOURCE_BASELINE.json"

ALLOWED_ITEM_STATES = {
    "not_started",
    "in_progress",
    "evidence_ready",
    "in_review",
    "blocked",
    "failed",
    "passed",
}
ALLOWED_STAGE_STATES = ALLOWED_ITEM_STATES | {"blocked_entry_conditions"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_ID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
PINNED_PRIVATE_SOURCE_RE = re.compile(
    r"^https://github\.com/Mr-Harsh-Dixit/AI-Resume-Platform-Sources/blob/"
    r"(?P<commit>[0-9a-f]{40}|[0-9a-f]{64})/sources/(?:handbook|specification)/.+$"
)
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")


class ControlPlaneError(ValueError):
    """Raised when a control-plane invariant is violated."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ControlPlaneError(f"Missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ControlPlaneError(
            f"Invalid JSON in {path.relative_to(ROOT)} at line {exc.lineno}: {exc.msg}"
        ) from exc

    if not isinstance(value, dict):
        raise ControlPlaneError(f"Top-level JSON value must be an object: {path.relative_to(ROOT)}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ControlPlaneError(message)


def ensure_unique_ids(items: list[dict[str, Any]], label: str) -> None:
    ids = [item.get("id") for item in items]
    require(all(isinstance(item_id, str) and item_id for item_id in ids), f"{label} IDs must be non-empty strings")
    require(len(ids) == len(set(ids)), f"{label} IDs must be unique")


def validate_state(item: dict[str, Any], allowed: set[str], label: str) -> None:
    state = item.get("state")
    require(state in allowed, f"{label} has unsupported state: {state!r}")


def validate_no_private_paths(value: Any, location: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            validate_no_private_paths(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_no_private_paths(child, f"{location}[{index}]")
    elif isinstance(value, str):
        require(
            not WINDOWS_ABSOLUTE_PATH_RE.match(value),
            f"Absolute workstation path is forbidden at {location}",
        )


def validate_baseline(baseline: dict[str, Any]) -> None:
    require(baseline.get("schema_version") == "1.0.0", "Unsupported source baseline schema version")
    require(baseline.get("hash_algorithm") == "sha256", "Source baseline must use SHA-256")
    require(
        baseline.get("baseline_state") in ALLOWED_ITEM_STATES,
        "Source baseline has unsupported state",
    )

    sources = baseline.get("authoritative_sources")
    require(isinstance(sources, list) and len(sources) >= 2, "At least two authoritative sources are required")
    source_ids = [source.get("source_id") for source in sources]
    require(len(source_ids) == len(set(source_ids)), "Source IDs must be unique")
    storage_commits: set[str] = set()

    for source in sources:
        source_id = source.get("source_id", "<unknown>")
        require(SHA256_RE.fullmatch(str(source.get("sha256", ""))) is not None, f"{source_id} has an invalid SHA-256")
        require(source.get("filename"), f"{source_id} is missing filename")
        require(source.get("version"), f"{source_id} is missing version")
        if source.get("storage_state") == "complete":
            storage_uri = source.get("controlled_storage_uri")
            require(storage_uri, f"{source_id} storage is complete without a URI")
            storage_match = PINNED_PRIVATE_SOURCE_RE.fullmatch(str(storage_uri))
            require(
                storage_match is not None,
                f"{source_id} storage URI must pin an immutable private-source commit",
            )
            storage_commits.add(storage_match.group("commit"))
            require(
                source.get("repository_copy_authorized") is True,
                f"{source_id} storage is complete without repository-copy authorization",
            )

    if baseline.get("baseline_state") in {"evidence_ready", "passed"}:
        require(
            all(source.get("storage_state") == "complete" for source in sources),
            "Evidence-ready source baseline contains incomplete storage",
        )
        controlled_storage = baseline.get("controlled_storage")
        require(isinstance(controlled_storage, dict), "Evidence-ready source baseline lacks controlled-storage metadata")
        require(controlled_storage.get("visibility") == "private", "Controlled source repository must be private")
        require(controlled_storage.get("verification_result") == "passed", "Controlled source verification has not passed")
        commit_sha = str(controlled_storage.get("commit_sha", ""))
        require(GIT_OBJECT_ID_RE.fullmatch(commit_sha) is not None, "Controlled source commit ID is invalid")
        require(storage_commits == {commit_sha}, "Pinned source URIs do not match the controlled source commit")

    validate_no_private_paths(baseline)


def validate_pass_evidence(item: dict[str, Any], label: str) -> None:
    if item.get("state") != "passed":
        return

    review = item.get("review")
    github = item.get("github_checkpoint") or item.get("github")
    require(isinstance(review, dict), f"{label} passed without review evidence")
    require(review.get("verdict") == "PASS", f"{label} passed without an independent PASS")
    require(review.get("reviewer"), f"{label} passed without reviewer identity")
    require(review.get("verdict_on"), f"{label} passed without review date")
    builder = item.get("builder") or review.get("builder")
    if builder:
        require(builder != review.get("reviewer"), f"{label} was self-approved by its builder")
    require(isinstance(github, dict), f"{label} passed without GitHub evidence")
    require(
        GIT_OBJECT_ID_RE.fullmatch(str(github.get("commit_sha", ""))) is not None,
        f"{label} passed without a full Git object ID",
    )
    github_url = github.get("url") or github.get("pull_request_url")
    require(str(github_url or "").startswith("https://github.com/"), f"{label} passed without a GitHub URL")
    require(not item.get("blocked_by"), f"{label} passed while blockers remain recorded")


def validate_status(status: dict[str, Any], baseline: dict[str, Any]) -> None:
    require(status.get("schema_version") == "1.0.0", "Unsupported status schema version")
    require(status.get("stage_id") == "S0", "Status file must describe Stage 0")
    require(status.get("stage_state") in ALLOWED_STAGE_STATES, "Stage has unsupported state")
    require(
        status.get("source_specification", {}).get("source_baseline_id") == baseline.get("baseline_id"),
        "Status and source baseline IDs do not match",
    )

    entry_conditions = status.get("entry_conditions")
    steps = status.get("steps")
    exits = status.get("exit_criteria")
    require(isinstance(entry_conditions, list), "entry_conditions must be a list")
    require(isinstance(steps, list), "steps must be a list")
    require(isinstance(exits, list), "exit_criteria must be a list")

    ensure_unique_ids(entry_conditions, "Entry condition")
    ensure_unique_ids(steps, "Step")
    ensure_unique_ids(exits, "Exit criterion")

    expected_steps = {f"S0-{index:02d}" for index in range(1, 15)}
    expected_exits = {f"S0-EXIT-{index:02d}" for index in range(1, 9)}
    require({step["id"] for step in steps} == expected_steps, "Stage 0 must contain exactly steps S0-01 through S0-14")
    require({item["id"] for item in exits} == expected_exits, "Stage 0 must contain exactly exits S0-EXIT-01 through S0-EXIT-08")

    for item in entry_conditions:
        validate_state(item, ALLOWED_ITEM_STATES, item["id"])
    for item in steps:
        validate_state(item, ALLOWED_ITEM_STATES, item["id"])
        validate_pass_evidence(item, item["id"])
    for item in exits:
        validate_state(item, ALLOWED_ITEM_STATES, item["id"])

    if status.get("stage_state") == "passed":
        require(all(item.get("state") == "passed" for item in exits), "Stage passed while an exit criterion is not passed")
        validate_pass_evidence(status, "Stage S0")

    validate_no_private_paths(status)


def verify() -> None:
    baseline = load_json(BASELINE_PATH)
    status = load_json(STATUS_PATH)
    validate_baseline(baseline)
    validate_status(status, baseline)


def main() -> int:
    try:
        verify()
    except ControlPlaneError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: Stage 0 control-plane integrity checks succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
