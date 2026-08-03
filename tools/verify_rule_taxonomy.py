"""Fail-closed validation for the versioned Stage 0 rule taxonomy."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "rulebook" / "taxonomy" / "1.0.0" / "taxonomy.json"
SEMANTIC_LOCK_PATH = ROOT / "rulebook" / "taxonomy" / "1.0.0" / "semantic-lock.json"
SCHEMA_PATH = ROOT / "rulebook" / "schemas" / "rule-taxonomy.schema.json"
LOCATOR_INDEX_PATH = ROOT / "rulebook" / "sources" / "1.0.0" / "source-locator-index.json"
BASELINE_PATH = ROOT / "docs" / "stage-0" / "SOURCE_BASELINE.json"

PINNED_JSONSCHEMA_VERSION = "4.26.0"
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
    "ai_authority_policy",
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
SOURCE_REFERENCE_KEYS = {"source_id", "source_sha256", "pages", "sections", "purpose"}
SEMANTIC_FIELDS = (
    "schema_version",
    "taxonomy_id",
    "taxonomy_version",
    "source_baseline_id",
    "primary_class_cardinality",
    "classes",
    "decision_sequence",
    "context_axes",
    "global_invariants",
    "unclassified_result",
    "ai_authority_policy",
    "change_policy",
    "source_references",
)
EXPECTED_AI_AUTHORITY_POLICY = {
    "prompt_reclassification_forbidden": True,
    "model_output_authority": "provisional_structured_data",
    "deterministic_validation_required": True,
}
EXPECTED_LOCK_CHANGE_POLICY = {
    "same_version_semantic_change": "reject",
    "new_version_required": True,
    "fresh_review_required": True,
}
SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
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


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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


def schema_error_location(error: Any) -> str:
    location = "$"
    for part in error.absolute_path:
        location += f"[{part}]" if isinstance(part, int) else f".{part}"
    return location


def validate_with_json_schema(schema: dict[str, Any], taxonomy: dict[str, Any]) -> None:
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ModuleNotFoundError as exc:
        raise TaxonomyError(
            "Missing pinned verification dependency; install requirements/verification.txt"
        ) from exc

    require(
        importlib.metadata.version("jsonschema") == PINNED_JSONSCHEMA_VERSION,
        f"jsonschema must be pinned to {PINNED_JSONSCHEMA_VERSION}",
    )
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise TaxonomyError(f"Invalid Draft 2020-12 taxonomy schema: {exc.message}") from exc

    errors = sorted(
        Draft202012Validator(schema).iter_errors(taxonomy),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        first = errors[0]
        raise TaxonomyError(
            f"Taxonomy JSON Schema validation failed at {schema_error_location(first)}: {first.message}"
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
            len(item["prohibited_uses"]) == len(set(item["prohibited_uses"])),
            f"{class_id} contains duplicate prohibited uses",
        )
        require(
            set(item["exception_policy"]) == {"allowed", "required_evidence"},
            f"{class_id} exception policy has an invalid shape",
        )

    require(classes["hard"]["exception_policy"]["allowed"] is False, "Hard rules cannot have exceptions")
    require(
        "override_by_prompt_or_aesthetic_preference" in classes["hard"]["prohibited_uses"],
        "Hard rules must explicitly prohibit prompt or aesthetic overrides",
    )
    require("hard" in classes["scoring"].get("cannot_override", []), "Scoring must not override hard rules")
    require(
        "compensate_for_hard_failure" in classes["scoring"].get("prohibited_uses", []),
        "Scoring must explicitly prohibit hard-failure compensation",
    )
    require(classes["strong_default"]["exception_policy"]["allowed"] is True, "Strong defaults need an exception contract")
    required_exception_evidence = set(classes["strong_default"]["exception_policy"]["required_evidence"])
    require(
        required_exception_evidence
        == {"exception_reason", "exception_authority", "applicable_context", "regression_test"},
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
        set(ids) == {f"TAX-INV-{index:03d}" for index in range(1, 10)},
        "Taxonomy must define invariants TAX-INV-001 through TAX-INV-009",
    )
    prompt_invariant = next(item for item in invariants if item["invariant_id"] == "TAX-INV-009")
    require(
        prompt_invariant
        == {
            "invariant_id": "TAX-INV-009",
            "statement": "AI prompts and model output cannot alter, bypass, or reclassify approved rule semantics.",
            "failure_result": "reject_ai_override",
        },
        "Prompt-reclassification invariant must remain machine-enforced",
    )


def validate_ai_authority_policy(taxonomy: dict[str, Any]) -> None:
    require(
        taxonomy.get("ai_authority_policy") == EXPECTED_AI_AUTHORITY_POLICY,
        "AI authority policy must forbid prompt reclassification and require deterministic validation",
    )


def baseline_page_count(source: dict[str, Any]) -> Any:
    if "page_count" in source:
        return source["page_count"]
    return source.get("rendered_page_count")


def index_baseline_sources(baseline: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources = baseline.get("authoritative_sources")
    require(isinstance(sources, list) and sources, "Frozen baseline must contain authoritative sources")
    require(all(isinstance(source, dict) for source in sources), "Baseline sources must be objects")
    source_ids = [source.get("source_id") for source in sources]
    require(
        all(isinstance(source_id, str) and source_id for source_id in source_ids),
        "Baseline source IDs must be non-empty strings",
    )
    require(len(source_ids) == len(set(source_ids)), "Baseline source IDs must be unique")
    for source in sources:
        require(
            SHA256_RE.fullmatch(str(source.get("sha256", ""))) is not None,
            f"{source.get('source_id')} baseline checksum is invalid",
        )
    return {source["source_id"]: source for source in sources}


def validate_locator_index(
    locator_index: dict[str, Any], baseline: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    require(
        set(locator_index) == {"schema_version", "source_baseline_id", "verification", "sources"},
        "Source locator index has unknown or missing root fields",
    )
    require(locator_index.get("schema_version") == "1.0.0", "Unsupported source locator index version")
    require(
        locator_index.get("source_baseline_id") == baseline.get("baseline_id"),
        "Source locator index does not match the Stage 0 baseline",
    )
    verification = locator_index.get("verification")
    require(
        isinstance(verification, dict)
        and set(verification) == {"method", "reviewed_on", "evidence_path"},
        "Source locator verification record is incomplete",
    )
    require(verification.get("method") == "manual_source_review", "Source locators lack manual verification")
    require(verification.get("reviewed_on"), "Source locator verification lacks a date")
    require(
        str(verification.get("evidence_path", "")).startswith("docs/stage-0/evidence/"),
        "Source locator verification lacks repository evidence",
    )

    baseline_sources = index_baseline_sources(baseline)
    sources = locator_index.get("sources")
    require(isinstance(sources, list) and sources, "Source locator index must contain sources")
    require(all(isinstance(source, dict) for source in sources), "Every locator source must be an object")
    source_ids = [source.get("source_id") for source in sources]
    require(
        all(isinstance(source_id, str) and source_id for source_id in source_ids),
        "Source locator IDs must be non-empty strings",
    )
    require(len(source_ids) == len(set(source_ids)), "Source locator IDs must be unique")
    require(set(source_ids) == set(baseline_sources), "Source locator index must cover the frozen sources exactly")

    indexed: dict[str, dict[str, Any]] = {}
    for source in sources:
        source_id = source["source_id"]
        require(
            set(source) == {"source_id", "source_sha256", "page_count", "locators"},
            f"{source_id} locator record has unknown or missing fields",
        )
        baseline_source = baseline_sources[source_id]
        require(
            source.get("source_sha256") == baseline_source.get("sha256"),
            f"{source_id} locator checksum does not match the frozen baseline",
        )
        expected_page_count = baseline_page_count(baseline_source)
        require(
            isinstance(expected_page_count, int) and expected_page_count > 0,
            f"{source_id} baseline lacks a valid page count",
        )
        require(source.get("page_count") == expected_page_count, f"{source_id} locator page count drifted")
        locators = source.get("locators")
        require(isinstance(locators, list) and locators, f"{source_id} must define controlled locators")
        require(all(isinstance(locator, dict) for locator in locators), f"{source_id} locators must be objects")
        sections = [locator.get("section") for locator in locators]
        require(
            all(isinstance(section, str) and section for section in sections),
            f"{source_id} locator sections must be non-empty strings",
        )
        require(len(sections) == len(set(sections)), f"{source_id} locator sections must be unique")
        section_pages: dict[str, set[int]] = {}
        for locator in locators:
            require(
                set(locator) == {"section", "pages"},
                f"{source_id} locator has unknown or missing fields",
            )
            section = locator.get("section")
            pages = locator.get("pages")
            require(isinstance(section, str) and section, f"{source_id} locator section is empty")
            require(isinstance(pages, list) and pages, f"{source_id} {section} lacks pages")
            require(
                all(isinstance(page, int) for page in pages),
                f"{source_id} {section} pages must be integers",
            )
            require(pages == sorted(set(pages)), f"{source_id} {section} pages must be sorted and unique")
            require(
                all(isinstance(page, int) and 1 <= page <= expected_page_count for page in pages),
                f"{source_id} {section} contains an out-of-range page",
            )
            section_pages[section] = set(pages)
        indexed[source_id] = {
            "source_sha256": source["source_sha256"],
            "page_count": expected_page_count,
            "section_pages": section_pages,
        }

    reject_private_paths(locator_index)
    return indexed


def validate_sources(
    taxonomy: dict[str, Any],
    baseline: dict[str, Any],
    indexed_locators: dict[str, dict[str, Any]],
) -> None:
    require(
        taxonomy.get("source_baseline_id") == baseline.get("baseline_id"),
        "Taxonomy source baseline does not match the Stage 0 manifest",
    )
    baseline_sources = index_baseline_sources(baseline)
    references = taxonomy.get("source_references")
    require(isinstance(references, list) and references, "Taxonomy needs source references")
    require(all(isinstance(reference, dict) for reference in references), "Source references must be objects")
    reference_ids = [reference.get("source_id") for reference in references]
    require(len(reference_ids) == len(set(reference_ids)), "Taxonomy source references must be unique")
    require(set(reference_ids) == set(baseline_sources), "Taxonomy must reference the frozen sources exactly")

    for reference in references:
        source_id = reference["source_id"]
        require(set(reference) == SOURCE_REFERENCE_KEYS, "Source references must reject unknown or missing fields")
        baseline_source = baseline_sources[source_id]
        locator = indexed_locators[source_id]
        require(
            reference.get("source_sha256") == baseline_source.get("sha256") == locator["source_sha256"],
            f"{source_id} taxonomy checksum does not match the frozen baseline",
        )
        require(SHA256_RE.fullmatch(reference["source_sha256"]) is not None, f"{source_id} checksum is invalid")
        pages = reference.get("pages")
        require(isinstance(pages, list) and pages, f"{source_id} reference is missing pages")
        require(pages == sorted(set(pages)), f"{source_id} pages must be sorted and unique")
        require(
            all(isinstance(page, int) and 1 <= page <= locator["page_count"] for page in pages),
            f"{source_id} contains an out-of-range page",
        )
        sections = reference.get("sections")
        require(isinstance(sections, list) and sections, f"{source_id} reference is missing sections")
        require(len(sections) == len(set(sections)), f"{source_id} sections must be unique")
        unknown_sections = set(sections) - set(locator["section_pages"])
        require(not unknown_sections, f"{source_id} references an unknown controlled section")
        expected_pages: set[int] = set()
        for section in sections:
            expected_pages.update(locator["section_pages"][section])
        require(
            set(pages) == expected_pages,
            f"{source_id} pages do not match the controlled section locators",
        )


def validate_semantic_lock(
    taxonomy: dict[str, Any], semantic_lock: dict[str, Any], locator_index: dict[str, Any]
) -> None:
    require(
        set(semantic_lock)
        == {
            "schema_version",
            "taxonomy_id",
            "taxonomy_version",
            "fingerprint_algorithm",
            "fingerprinted_fields",
            "semantic_sha256",
            "source_locator_index_sha256",
            "change_policy",
        },
        "Taxonomy semantic lock has unknown or missing fields",
    )
    require(semantic_lock.get("schema_version") == "1.0.0", "Unsupported semantic lock version")
    require(semantic_lock.get("taxonomy_id") == taxonomy.get("taxonomy_id"), "Semantic lock taxonomy ID mismatch")
    require(
        semantic_lock.get("taxonomy_version") == taxonomy.get("taxonomy_version"),
        "Semantic lock taxonomy version mismatch",
    )
    require(
        semantic_lock.get("fingerprint_algorithm") == "sha256-canonical-json",
        "Semantic lock must use canonical JSON SHA-256",
    )
    require(
        semantic_lock.get("fingerprinted_fields") == list(SEMANTIC_FIELDS),
        "Semantic lock field coverage is incomplete",
    )
    require(
        semantic_lock.get("change_policy") == EXPECTED_LOCK_CHANGE_POLICY,
        "Semantic lock must require a new version and fresh review",
    )
    semantic_fingerprint = canonical_sha256({field: taxonomy[field] for field in SEMANTIC_FIELDS})
    require(
        semantic_lock.get("semantic_sha256") == semantic_fingerprint,
        "Same-version taxonomy semantic fingerprint mismatch; create a new version and fresh review",
    )
    require(
        semantic_lock.get("source_locator_index_sha256") == canonical_sha256(locator_index),
        "Source locator index fingerprint mismatch; update it only through versioned fresh review",
    )
    reject_private_paths(semantic_lock)


def validate_taxonomy(
    taxonomy: dict[str, Any],
    schema: dict[str, Any],
    baseline: dict[str, Any],
    locator_index: dict[str, Any],
    semantic_lock: dict[str, Any],
) -> None:
    validate_schema_document(schema)
    validate_with_json_schema(schema, taxonomy)
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
    validate_ai_authority_policy(taxonomy)
    validate_classes(index_classes(taxonomy))
    validate_decision_sequence(taxonomy)
    validate_invariants(taxonomy)
    indexed_locators = validate_locator_index(locator_index, baseline)
    validate_sources(taxonomy, baseline, indexed_locators)
    validate_semantic_lock(taxonomy, semantic_lock, locator_index)
    reject_private_paths(taxonomy)
    reject_private_paths(schema)
    reject_private_paths(baseline)


def verify() -> None:
    validate_taxonomy(
        load_object(TAXONOMY_PATH),
        load_object(SCHEMA_PATH),
        load_object(BASELINE_PATH),
        load_object(LOCATOR_INDEX_PATH),
        load_object(SEMANTIC_LOCK_PATH),
    )


def main() -> int:
    try:
        verify()
    except TaxonomyError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("PASS: Rule taxonomy schema, semantic lock, and source bindings succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
