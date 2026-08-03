from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "verify_stage0_control_plane.py"
SPEC = importlib.util.spec_from_file_location("verify_stage0_control_plane", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
CONTROL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTROL)


class Stage0ControlPlaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.baseline = CONTROL.load_json(CONTROL.BASELINE_PATH)
        self.status = CONTROL.load_json(CONTROL.STATUS_PATH)

    def test_repository_control_plane_is_valid(self) -> None:
        CONTROL.validate_baseline(self.baseline)
        CONTROL.validate_status(self.status, self.baseline)

    def test_passed_step_requires_independent_review(self) -> None:
        status = copy.deepcopy(self.status)
        step = status["steps"][1]
        step["state"] = "passed"
        step.pop("review", None)
        step.pop("github_checkpoint", None)

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "review evidence"):
            CONTROL.validate_status(status, self.baseline)

    def test_passed_baseline_requires_review(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline.pop("review", None)

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "review evidence"):
            CONTROL.validate_baseline(baseline)

    def test_review_history_rejects_invalid_reviewed_commit(self) -> None:
        status = copy.deepcopy(self.status)
        status["steps"][2]["review_history"][0]["reviewed_commit"] = "short"

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "full reviewed Git object ID"):
            CONTROL.validate_status(status, self.baseline)

    def test_review_history_requires_retained_evidence(self) -> None:
        status = copy.deepcopy(self.status)
        status["steps"][2]["review_history"][0]["evidence"] = (
            "docs/stage-0/evidence/does-not-exist.md"
        )

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "missing review evidence"):
            CONTROL.validate_status(status, self.baseline)

    def test_passed_step_accepts_reviewed_sha1_git_checkpoint(self) -> None:
        status = copy.deepcopy(self.status)
        step = status["steps"][1]
        step["state"] = "passed"
        step["blocked_by"] = []
        step["builder"] = "builder@example.invalid"
        step["review"] = {
            "reviewer": "reviewer@example.invalid",
            "verdict": "PASS",
            "verdict_on": "2026-08-03",
        }
        step["github_checkpoint"] = {
            "state": "passed",
            "commit_sha": "a" * 40,
            "pull_request_url": "https://github.com/example/project/pull/1",
        }

        CONTROL.validate_status(status, self.baseline)

    def test_passed_step_rejects_self_approval(self) -> None:
        status = copy.deepcopy(self.status)
        step = status["steps"][1]
        step["state"] = "passed"
        step["blocked_by"] = []
        step["builder"] = "same@example.invalid"
        step["review"] = {
            "reviewer": "same@example.invalid",
            "verdict": "PASS",
            "verdict_on": "2026-08-03",
        }
        step["github_checkpoint"] = {
            "state": "passed",
            "commit_sha": "a" * 40,
            "pull_request_url": "https://github.com/example/project/pull/1",
        }

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "self-approved"):
            CONTROL.validate_status(status, self.baseline)

    def test_passed_stage_requires_every_exit_to_pass(self) -> None:
        status = copy.deepcopy(self.status)
        status["stage_state"] = "passed"

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "exit criterion"):
            CONTROL.validate_status(status, self.baseline)

    def test_source_manifest_rejects_absolute_workstation_paths(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["builder_inspection"]["notes"][0] = "C:\\Users\\example\\source.pdf"

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "Absolute workstation path"):
            CONTROL.validate_baseline(baseline)

    def test_complete_source_storage_requires_uri(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["authoritative_sources"][0]["controlled_storage_uri"] = None

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "without a URI"):
            CONTROL.validate_baseline(baseline)

    def test_complete_source_storage_rejects_mutable_branch_url(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["authoritative_sources"][0]["controlled_storage_uri"] = (
            "https://github.com/Mr-Harsh-Dixit/AI-Resume-Platform-Sources/blob/main/"
            "sources/handbook/1.0.0/source.pdf"
        )

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "immutable private-source commit"):
            CONTROL.validate_baseline(baseline)

    def test_complete_source_storage_requires_copy_authorization(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["authoritative_sources"][0]["repository_copy_authorized"] = False

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "copy authorization"):
            CONTROL.validate_baseline(baseline)

    def test_source_uris_must_match_controlled_storage_commit(self) -> None:
        baseline = copy.deepcopy(self.baseline)
        baseline["controlled_storage"]["commit_sha"] = "b" * 40

        with self.assertRaisesRegex(CONTROL.ControlPlaneError, "do not match"):
            CONTROL.validate_baseline(baseline)


if __name__ == "__main__":
    unittest.main()
