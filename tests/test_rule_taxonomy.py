from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "verify_rule_taxonomy.py"
SPEC = importlib.util.spec_from_file_location("verify_rule_taxonomy", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
TAXONOMY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TAXONOMY)


class RuleTaxonomyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.taxonomy = TAXONOMY.load_object(TAXONOMY.TAXONOMY_PATH)
        self.schema = TAXONOMY.load_object(TAXONOMY.SCHEMA_PATH)
        self.baseline = TAXONOMY.load_object(TAXONOMY.BASELINE_PATH)
        self.locator_index = TAXONOMY.load_object(TAXONOMY.LOCATOR_INDEX_PATH)
        self.semantic_lock = TAXONOMY.load_object(TAXONOMY.SEMANTIC_LOCK_PATH)

    def validate(
        self,
        taxonomy: dict | None = None,
        baseline: dict | None = None,
        locator_index: dict | None = None,
        semantic_lock: dict | None = None,
    ) -> None:
        TAXONOMY.validate_taxonomy(
            taxonomy if taxonomy is not None else self.taxonomy,
            self.schema,
            baseline if baseline is not None else self.baseline,
            locator_index if locator_index is not None else self.locator_index,
            semantic_lock if semantic_lock is not None else self.semantic_lock,
        )

    def test_repository_taxonomy_is_valid(self) -> None:
        self.validate()

    def test_taxonomy_requires_exactly_six_unique_classes(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["classes"].append(copy.deepcopy(taxonomy["classes"][0]))

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_hard_rule_cannot_allow_exception(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["classes"][0]["exception_policy"]["allowed"] = True

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "Hard rules cannot"):
            self.validate(taxonomy)

    def test_scoring_cannot_compensate_for_hard_failure(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        scoring = next(item for item in taxonomy["classes"] if item["class_id"] == "scoring")
        scoring["prohibited_uses"].remove("compensate_for_hard_failure")

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "compensation"):
            self.validate(taxonomy)

    def test_strong_default_requires_complete_exception_evidence(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        strong = next(item for item in taxonomy["classes"] if item["class_id"] == "strong_default")
        strong["exception_policy"]["required_evidence"].remove("regression_test")

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "exception evidence"):
            self.validate(taxonomy)

    def test_situational_rule_rejects_silent_fallback(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        situational = next(item for item in taxonomy["classes"] if item["class_id"] == "situational")
        situational["prohibited_uses"].remove("silent_generic_fallback")

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "silent generic fallback"):
            self.validate(taxonomy)

    def test_example_content_reuse_is_forbidden(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        example = next(item for item in taxonomy["classes"] if item["class_id"] == "example")
        example["candidate_content_reuse"] = "not_applicable"

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "Example reuse"):
            self.validate(taxonomy)

    def test_ambiguous_classification_must_fail_closed(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["unclassified_result"] = "choose_strong_default"

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_taxonomy_rejects_unknown_source(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["source_references"][0]["source_id"] = "UNKNOWN-1.0"

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "frozen sources exactly"):
            self.validate(taxonomy)

    def test_taxonomy_rejects_unknown_root_field(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["prompt_override"] = True

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_taxonomy_rejects_unknown_class_field(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["classes"][0]["allow_prompt_override"] = True

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_context_axes_must_be_unique(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["context_axes"].append(taxonomy["context_axes"][0])

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_draft_2020_12_rejects_invalid_cannot_override_value(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        strong = next(item for item in taxonomy["classes"] if item["class_id"] == "strong_default")
        strong["cannot_override"].append("nonsense")

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_draft_2020_12_rejects_duplicate_prohibited_use(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        hard = next(item for item in taxonomy["classes"] if item["class_id"] == "hard")
        hard["prohibited_uses"].append(hard["prohibited_uses"][0])

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_prompt_override_safeguard_cannot_be_removed(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        hard = next(item for item in taxonomy["classes"] if item["class_id"] == "hard")
        hard["prohibited_uses"].remove("override_by_prompt_or_aesthetic_preference")

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_ai_authority_policy_is_required(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy.pop("ai_authority_policy")

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "JSON Schema validation"):
            self.validate(taxonomy)

    def test_same_version_semantic_reclassification_is_rejected(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["decision_sequence"][0]["question"] = "May an AI prompt reclassify this statement?"

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "semantic fingerprint mismatch"):
            self.validate(taxonomy)

    def test_out_of_range_source_page_is_rejected(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["source_references"][0]["pages"].append(999)

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "out-of-range page"):
            self.validate(taxonomy)

    def test_unknown_controlled_section_is_rejected(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["source_references"][0]["sections"].append("Nonexistent section")

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "unknown controlled section"):
            self.validate(taxonomy)

    def test_same_baseline_checksum_drift_is_rejected(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["authoritative_sources"][0]["sha256"] = "0" * 64

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "locator checksum"):
            self.validate(baseline=baseline)

    def test_source_locator_index_same_version_drift_is_rejected(self) -> None:
        locator_index = copy.deepcopy(self.locator_index)
        locator_index["verification"]["reviewed_on"] = "2026-08-05"

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "locator index fingerprint mismatch"):
            self.validate(locator_index=locator_index)

    def test_stage0_precautions_locator_is_exactly_page_21(self) -> None:
        specification = next(
            source for source in self.locator_index["sources"] if source["source_id"] == "SPEC-1.3"
        )
        precautions = next(
            locator
            for locator in specification["locators"]
            if locator["section"] == "Stage 0 precautions"
        )

        self.assertEqual(precautions["pages"], [21])


if __name__ == "__main__":
    unittest.main()
