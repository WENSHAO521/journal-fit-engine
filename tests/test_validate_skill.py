"""Negative-path checks for scripts/validate_skill.py, run out-of-process
against isolated temporary copies of the repository; no network calls.

validate_skill.py keeps its check state in module globals (errors/warnings)
rather than returning them from a pure function, so these tests drive it the
same way CI does: as a subprocess against a real file tree, asserting on
exit code and printed diagnostics.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_skill.py"

TRACKED_FILES = (
    "CHANGELOG.md", "LICENSE", "README.md", "SKILL.md", "VERSION",
    "RELEASE_CHECKLIST.md",
    "agents/openai.yaml",
    "disciplines/education.md", "disciplines/engineering-computing.md",
    "disciplines/humanities.md", "disciplines/interdisciplinary.md",
    "disciplines/law.md", "disciplines/management.md",
    "disciplines/mathematics.md", "disciplines/medicine-health.md",
    "disciplines/natural-sciences.md", "disciplines/social-sciences.md",
    "evals/current-data.jsonl", "evals/fit-ranking.jsonl",
    "evals/hard-filter.jsonl", "evals/integrity-cases.jsonl",
    "evals/manuscript-profile.jsonl", "evals/strategy-cases.jsonl",
    "references/adaptation-policy.md", "references/apc-open-access.md",
    "references/candidate-generation.md", "references/evidence-policy.md",
    "references/fit-model.md", "references/indexing-metrics.md",
    "references/integration.md", "references/journal-integrity.md",
    "references/journal-profile.md", "references/manuscript-profile.md",
    "references/submission-strategy.md",
    "scripts/validate_skill.py", "scripts/package_runtime.py",
    "tests/test_validate_skill.py", "tests/test_package_runtime.py",
    ".github/workflows/validate.yml",
)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in TRACKED_FILES:
            src = ROOT / relative
            if not src.is_file():
                continue
            dst = self.root / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    def edit(self, relative, transform):
        path = self.root / relative
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8")

    def run_validator(self):
        return subprocess.run(
            [sys.executable, str(self.root / "scripts" / "validate_skill.py")],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8")

    def reject(self, message):
        result = self.run_validator()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)

    def accept(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def edit_eval_first_record(self, name, mutate):
        def change(text):
            lines = text.splitlines()
            record = json.loads(lines[0])
            mutate(record)
            lines[0] = json.dumps(record)
            return "\n".join(lines) + "\n"
        self.edit(f"evals/{name}", change)

    def test_clean_repository(self):
        stdout = self.accept()
        self.assertIn("OK: all validation checks passed.", stdout)

    def test_missing_required_top_file(self):
        (self.root / "README.md").unlink()
        self.reject("Missing required top-level file: README.md")

    def test_missing_reference_file(self):
        (self.root / "references/fit-model.md").unlink()
        self.reject("Missing required reference file: references/fit-model.md")

    def test_missing_discipline_file(self):
        (self.root / "disciplines/law.md").unlink()
        self.reject("Missing required discipline file: disciplines/law.md")

    def test_missing_eval_file(self):
        (self.root / "evals/hard-filter.jsonl").unlink()
        self.reject("Missing required eval file: evals/hard-filter.jsonl")

    def test_missing_agents_yaml(self):
        (self.root / "agents/openai.yaml").unlink()
        self.reject("Missing agents/openai.yaml")

    def test_skill_frontmatter_wrong_name(self):
        self.edit("SKILL.md", lambda text: text.replace(
            "name: journal-fit-engine", "name: something-else", 1))
        self.reject("SKILL.md frontmatter 'name' should be 'journal-fit-engine'")

    def test_skill_frontmatter_missing_description(self):
        self.edit("SKILL.md", lambda text: "\n".join(
            line for line in text.splitlines() if not line.startswith("description:")))
        self.reject("missing a non-empty 'description'")

    def test_skill_missing_frontmatter_block(self):
        self.edit("SKILL.md", lambda text: text.split("---\n", 2)[-1])
        self.reject("missing a --- frontmatter block")

    def test_agents_yaml_missing_name_key(self):
        self.edit("agents/openai.yaml", lambda text: text.replace(
            "name: journal-fit-engine\n", "", 1))
        self.reject("missing top-level 'name:' key")

    def test_agents_yaml_missing_description_key(self):
        self.edit("agents/openai.yaml", lambda text: text.replace("description:", "desc:", 1))
        self.reject("missing top-level 'description:' key")

    def test_broken_local_link_in_skill(self):
        self.edit("SKILL.md", lambda text: text + "\n[Missing](references/does-not-exist.md)\n")
        self.reject("Broken local link in SKILL.md")

    def test_broken_local_link_in_reference(self):
        self.edit("references/fit-model.md",
                   lambda text: text + "\n[Missing](nonexistent-file.md)\n")
        self.reject("Broken local link in references")

    def test_remote_link_not_checked(self):
        self.edit("SKILL.md", lambda text: text + "\n[Example](https://example.com/not-checked)\n")
        self.accept()

    def test_malformed_jsonl_record(self):
        self.edit("evals/manuscript-profile.jsonl", lambda text: "{not json}\n" + text)
        self.reject("invalid JSON")

    def test_eval_missing_required_field(self):
        self.edit_eval_first_record("hard-filter.jsonl", lambda record: record.pop("expected_behavior"))
        self.reject("record missing required fields")

    def test_eval_expected_behavior_must_be_nonempty_list(self):
        self.edit_eval_first_record(
            "fit-ranking.jsonl", lambda record: record.update(expected_behavior="not-a-list"))
        self.reject("'expected_behavior' must be a non-empty list")

    def test_duplicate_id_within_file(self):
        def change(text):
            lines = [line for line in text.splitlines() if line.strip()]
            first = json.loads(lines[0])
            second = json.loads(lines[1])
            second["id"] = first["id"]
            lines[1] = json.dumps(second)
            return "\n".join(lines) + "\n"
        self.edit("evals/integrity-cases.jsonl", change)
        self.reject("duplicate id within file")

    def test_duplicate_id_across_files(self):
        first_line = (self.root / "evals/current-data.jsonl").read_text(encoding="utf-8").splitlines()[0]
        first_id = json.loads(first_line)["id"]
        self.edit_eval_first_record("strategy-cases.jsonl", lambda record: record.update(id=first_id))
        self.reject("duplicate id across files")

    def test_eval_count_below_minimum_is_rejected(self):
        (self.root / "evals/current-data.jsonl").write_text("", encoding="utf-8")
        self.reject("is below required minimum")

    def test_eval_count_at_minimum_is_a_warning_not_a_failure(self):
        stdout = self.accept()
        self.assertIn("Total eval cases:", stdout)

    def test_manuscript_profile_schema_marker_required(self):
        self.edit("references/manuscript-profile.md",
                   lambda text: text.replace("discipline:", "field:"))
        self.reject("does not appear to contain the manuscript profile schema")

    def test_journal_profile_schema_marker_required(self):
        self.edit("references/journal-profile.md",
                   lambda text: text.replace("issn:", "identifier:"))
        self.reject("does not appear to contain the journal profile schema")

    def test_version_must_be_plain_semver(self):
        self.edit("VERSION", lambda text: "v0.1.0")
        self.reject("VERSION must contain a plain MAJOR.MINOR.PATCH version")

    def test_version_changelog_mismatch_rejected(self):
        self.edit("VERSION", lambda text: "9.9.9")
        self.reject("VERSION (9.9.9) and latest CHANGELOG.md heading (0.1.0) disagree")

    def test_missing_version_file_is_required_file_error(self):
        (self.root / "VERSION").unlink()
        self.reject("Missing required top-level file: VERSION")


if __name__ == "__main__":
    unittest.main()
