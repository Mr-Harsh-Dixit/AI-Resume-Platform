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

    def validate(self, taxonomy: dict | None = None) -> None:
        TAXONOMY.validate_taxonomy(taxonomy or self.taxonomy, self.schema, self.baseline)

    def test_repository_taxonomy_is_valid(self) -> None:
        self.validate()

    def test_taxonomy_requires_exactly_six_unique_classes(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["classes"].append(copy.deepcopy(taxonomy["classes"][0]))

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "unique"):
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

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "fail closed"):
            self.validate(taxonomy)

    def test_taxonomy_rejects_unknown_source(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["source_references"][0]["source_id"] = "UNKNOWN-1.0"

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "unknown source"):
            self.validate(taxonomy)

    def test_taxonomy_rejects_unknown_root_field(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["prompt_override"] = True

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "root"):
            self.validate(taxonomy)

    def test_taxonomy_rejects_unknown_class_field(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["classes"][0]["allow_prompt_override"] = True

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "unknown fields"):
            self.validate(taxonomy)

    def test_context_axes_must_be_unique(self) -> None:
        taxonomy = copy.deepcopy(self.taxonomy)
        taxonomy["context_axes"].append(taxonomy["context_axes"][0])

        with self.assertRaisesRegex(TAXONOMY.TaxonomyError, "Context axes must be unique"):
            self.validate(taxonomy)


if __name__ == "__main__":
    unittest.main()
