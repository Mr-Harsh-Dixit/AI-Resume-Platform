"""Dependency-free semantic validation for the versioned rule taxonomy."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "rulebook" / "taxonomy" / "1.0.0" / "taxonomy.json"
SCHEMA_PATH = ROOT / "rulebook" / "schemas" / "rule-taxonomy.schema.json"
BASELINE_PATH = ROOT / "docs" / "stage-0" / "SOURCE_BASELINE.json"

EXPECTED_CLASS_MODES = {
    "hard": ("enforceable", "block"),
    "strong_default": ("enforceable", "apply_unless_exception"),
    "situational": ("enforceable", "evaluate_context"),
    "scoring": ("diagnostic", "score_only"),
    "example": ("non_actionable", "never_execute"),
    "explanatory": ("non_actionable", "never_execute"),
}
EXPECTED_ROOT_KEYS = {
    "$schema",
    "schema_version",
    "taxonomy_id",
    "taxonomy_version",
    "status",
    "source_baseline_id",
    "primary_class_cardinality",
    "classes",
    "decision_sequence",
    "context_axes",
    "global_invariants",
    "unclassified_result",
    "change_policy",
    "source_references",
}
REQUIRED_CLASS_KEYS = {
    "class_id",
    "description",
    "classification_question",
    "actionability",
    "enforcement_mode",
    "context_required",
    "exception_policy",
    "required_rule_fields",
    "prohibited_uses",
}
OPTIONAL_CLASS_KEYS = {"cannot_override", "candidate_content_reuse"}
SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")


class TaxonomyError(ValueError):
    """Raised when taxonomy data violates a fail-closed invariant."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise TaxonomyError(message)


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise TaxonomyError(f"Missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise TaxonomyError(
            f"Invalid JSON in {path.relative_to(ROOT)} at line {exc.lineno}: {exc.msg}"
        ) from exc
    require(isinstance(value, dict), f"Top-level value must be an object: {path.relative_to(ROOT)}")
    return value


def reject_private_paths(value: Any, location: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            reject_private_paths(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_paths(child, f"{location}[{index}]")
    elif isinstance(value, str):
        require(
            WINDOWS_ABSOLUTE_PATH_RE.match(value) is None,
            f"Absolute workstation path is forbidden at {location}",
        )


def validate_schema_document(schema: dict[str, Any]) -> None:
    require(
        schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        "Taxonomy schema must use JSON Schema Draft 2020-12",
    )
    require(schema.get("type") == "object", "Taxonomy schema root must be an object")
    require(schema.get("additionalProperties") is False, "Taxonomy schema must reject unknown root fields")
    require("ruleClass" in schema.get("$defs", {}), "Taxonomy schema is missing ruleClass definition")


def index_classes(taxonomy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    classes = taxonomy.get("classes")
    require(isinstance(classes, list), "classes must be a list")
    require(all(isinstance(item, dict) for item in classes), "Every class must be an object")
    ids = [item.get("class_id") for item in classes]
    require(len(ids) == len(set(ids)), "Class IDs must be unique")
    require(set(ids) == set(EXPECTED_CLASS_MODES), "Taxonomy must define exactly the six approved classes")
    return {item["class_id"]: item for item in classes}


def validate_classes(classes: dict[str, dict[str, Any]]) -> None:
    for class_id, (actionability, enforcement_mode) in EXPECTED_CLASS_MODES.items():
        item = classes[class_id]
        require(REQUIRED_CLASS_KEYS <= set(item), f"{class_id} is missing required fields")
        require(
            set(item) <= REQUIRED_CLASS_KEYS | OPTIONAL_CLASS_KEYS,
            f"{class_id} contains unknown fields",
        )
        require(item.get("actionability") == actionability, f"{class_id} has incorrect actionability")
        require(item.get("enforcement_mode") == enforcement_mode, f"{class_id} has incorrect enforcement mode")
        require(item.get("description"), f"{class_id} is missing description")
        require(item.get("classification_question"), f"{class_id} is missing classification question")
        require(item.get("required_rule_fields"), f"{class_id} is missing required rule fields")
        require(
            len(item["required_rule_fields"]) == len(set(item["required_rule_fields"])),
            f"{class_id} contains duplicate required rule fields",
        )
        require(
            all(SNAKE_CASE_RE.fullmatch(field) for field in item["required_rule_fields"]),
            f"{class_id} required rule fields must use snake_case",
        )
        require(isinstance(item.get("prohibited_uses"), list), f"{class_id} must declare prohibited uses")
        require(
            set(item["exception_policy"]) == {"allowed", "required_evidence"},
            f"{class_id} exception policy has an invalid shape",
        )

    require(classes["hard"]["exception_policy"]["allowed"] is False, "Hard rules cannot have exceptions")
    require("hard" in classes["scoring"].get("cannot_override", []), "Scoring must not override hard rules")
    require(
        "compensate_for_hard_failure" in classes["scoring"].get("prohibited_uses", []),
        "Scoring must explicitly prohibit hard-failure compensation",
    )
    require(classes["strong_default"]["exception_policy"]["allowed"] is True, "Strong defaults need an exception contract")
    required_exception_evidence = set(classes["strong_default"]["exception_policy"]["required_evidence"])
    require(
        required_exception_evidence == {
            "exception_reason",
            "exception_authority",
            "applicable_context",
            "regression_test",
        },
        "Strong-default exception evidence is incomplete",
    )
    require(classes["situational"]["context_required"] is True, "Situational rules require context")
    require(
        "silent_generic_fallback" in classes["situational"].get("prohibited_uses", []),
        "Situational rules must prohibit silent generic fallback",
    )
    require(classes["example"].get("candidate_content_reuse") == "forbidden", "Example reuse must be forbidden")
    require(classes["explanatory"].get("actionability") == "non_actionable", "Explanatory guidance cannot be executable")


def validate_decision_sequence(taxonomy: dict[str, Any]) -> None:
    decisions = taxonomy.get("decision_sequence")
    require(isinstance(decisions, list), "decision_sequence must be a list")
    require(
        all(set(decision) == {"order", "question", "class_on_yes"} for decision in decisions),
        "Decision records must reject unknown or missing fields",
    )
    orders = [decision.get("order") for decision in decisions]
    require(orders == list(range(1, len(decisions) + 1)), "Decision order must be contiguous and deterministic")
    selected_classes = [decision.get("class_on_yes") for decision in decisions]
    require(len(selected_classes) == len(set(selected_classes)), "Decision sequence must select each class once")
    require(set(selected_classes) == set(EXPECTED_CLASS_MODES), "Decision sequence must cover all classes")
    require(selected_classes[:2] == ["example", "explanatory"], "Non-actionable material must be classified before rules")


def validate_invariants(taxonomy: dict[str, Any]) -> None:
    invariants = taxonomy.get("global_invariants")
    require(isinstance(invariants, list), "global_invariants must be a list")
    require(
        all(set(item) == {"invariant_id", "statement", "failure_result"} for item in invariants),
        "Invariant records must reject unknown or missing fields",
    )
    ids = [item.get("invariant_id") for item in invariants]
    require(len(ids) == len(set(ids)), "Invariant IDs must be unique")
    require(
        set(ids) == {f"TAX-INV-{index:03d}" for index in range(1, 9)},
        "Taxonomy must define invariants TAX-INV-001 through TAX-INV-008",
    )


def validate_sources(taxonomy: dict[str, Any], baseline: dict[str, Any]) -> None:
    require(
        taxonomy.get("source_baseline_id") == baseline.get("baseline_id"),
        "Taxonomy source baseline does not match the Stage 0 manifest",
    )
    known_sources = {source.get("source_id") for source in baseline.get("authoritative_sources", [])}
    references = taxonomy.get("source_references")
    require(isinstance(references, list) and references, "Taxonomy needs source references")
    referenced_sources = {reference.get("source_id") for reference in references}
    require(referenced_sources <= known_sources, "Taxonomy references an unknown source")
    require({"HANDBOOK-1.0", "SPEC-1.3"} <= referenced_sources, "Both authoritative sources must be referenced")
    for reference in references:
        require(
            set(reference) == {"source_id", "pages", "sections", "purpose"},
            "Source references must reject unknown or missing fields",
        )
        require(reference.get("pages"), f"{reference.get('source_id')} reference is missing pages")
        require(
            all(isinstance(page, int) and page > 0 for page in reference["pages"]),
            f"{reference.get('source_id')} pages must be positive integers",
        )
        require(reference.get("sections"), f"{reference.get('source_id')} reference is missing sections")


def validate_taxonomy(
    taxonomy: dict[str, Any], schema: dict[str, Any], baseline: dict[str, Any]
) -> None:
    validate_schema_document(schema)
    require(set(taxonomy) == EXPECTED_ROOT_KEYS, "Taxonomy root must reject unknown or missing fields")
    require(taxonomy.get("schema_version") == "1.0.0", "Unsupported taxonomy schema version")
    require(taxonomy.get("taxonomy_id") == "resume-rule-taxonomy", "Unexpected taxonomy ID")
    require(SEMVER_RE.fullmatch(str(taxonomy.get("taxonomy_version", ""))) is not None, "Invalid taxonomy version")
    require(taxonomy.get("status") in {"candidate", "approved", "superseded"}, "Invalid taxonomy status")
    require(taxonomy.get("primary_class_cardinality") == "exactly_one", "Each record needs exactly one primary class")
    require(taxonomy.get("unclassified_result") == "reject_until_human_review", "Ambiguous classification must fail closed")
    context_axes = taxonomy.get("context_axes")
    require(isinstance(context_axes, list) and context_axes, "context_axes must be a non-empty list")
    require(len(context_axes) == len(set(context_axes)), "Context axes must be unique")
    require(all(SNAKE_CASE_RE.fullmatch(axis) for axis in context_axes), "Context axes must use snake_case")
    require(
        taxonomy.get("change_policy")
        == {
            "silent_reclassification_forbidden": True,
            "version_change_required": True,
            "review_required": True,
        },
        "Taxonomy change policy must require versioned review",
    )
    validate_classes(index_classes(taxonomy))
    validate_decision_sequence(taxonomy)
    validate_invariants(taxonomy)
    validate_sources(taxonomy, baseline)
    reject_private_paths(taxonomy)
    reject_private_paths(schema)


def verify() -> None:
    validate_taxonomy(
        load_object(TAXONOMY_PATH),
        load_object(SCHEMA_PATH),
        load_object(BASELINE_PATH),
    )


def main() -> int:
    try:
        verify()
    except TaxonomyError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: Rule taxonomy structural and semantic checks succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
