"""Packaging regression tests: build/verify use isolated temp roots and
temp output directories; no network or model calls, no writes under dist/."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

spec = importlib.util.spec_from_file_location("validate_skill", SCRIPTS / "validate_skill.py")
validate_skill = importlib.util.module_from_spec(spec)
sys.modules["validate_skill"] = validate_skill
spec.loader.exec_module(validate_skill)

spec = importlib.util.spec_from_file_location("package_runtime", SCRIPTS / "package_runtime.py")
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)

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
    ".github/workflows/validate.yml", ".github/workflows/live-check.yml",
    "jfe/__init__.py", "jfe/http_client.py", "jfe/manuscript_profile.py",
    "jfe/journal_evidence.py", "jfe/apc_oa.py", "jfe/hard_filters.py",
    "jfe/fit_model.py", "jfe/fit_dimensions.py", "jfe/integrity.py",
    "jfe/indexing.py", "jfe/style_context.py", "jfe/cli.py",
)


class PackagerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "src"
        for relative in TRACKED_FILES:
            src = ROOT / relative
            if not src.is_file():
                continue
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
        self.out_dir = Path(self.temp.name) / "dist"
        self.version = packager.release_version(self.root)

    def build(self):
        return packager.build(self.root, self.out_dir)

    def archive_path(self):
        return self.out_dir / f"journal-fit-engine-v{self.version}.zip"

    def test_build_produces_three_artifacts(self):
        archive = self.build()
        self.assertEqual(archive, self.archive_path())
        self.assertTrue(archive.is_file())
        self.assertTrue(archive.with_suffix(".zip.sha256").is_file())
        self.assertTrue((self.out_dir / "release-manifest.json").is_file())

    def test_archive_contains_exactly_allowlisted_members(self):
        archive = self.build()
        with zipfile.ZipFile(archive) as zipped:
            names = set(zipped.namelist())
        expected = {f"journal-fit-engine/{relative}" for relative in validate_skill.RUNTIME_FILES}
        self.assertEqual(names, expected)
        self.assertEqual(len(expected), len(validate_skill.RUNTIME_FILES))

    def test_archive_excludes_dev_only_files(self):
        archive = self.build()
        with zipfile.ZipFile(archive) as zipped:
            names = zipped.namelist()
        for excluded in ("CHANGELOG.md", "VERSION", "RELEASE_CHECKLIST.md"):
            self.assertNotIn(f"journal-fit-engine/{excluded}", names)
        self.assertFalse(any("evals/" in n or "scripts/" in n or "tests/" in n for n in names))

    def test_build_is_deterministic_byte_for_byte(self):
        first = self.build().read_bytes()
        second = packager.build(self.root, Path(self.temp.name) / "dist2").read_bytes()
        self.assertEqual(first, second)

    def test_checksum_sidecar_matches_archive(self):
        archive = self.build()
        digest = packager.sha256(archive.read_bytes())
        sidecar = archive.with_suffix(".zip.sha256").read_text(encoding="utf-8")
        self.assertEqual(sidecar, f"{digest}  {archive.name}\n")

    def test_manifest_matches_archive_and_files(self):
        archive = self.build()
        digest = packager.sha256(archive.read_bytes())
        record = json.loads((self.out_dir / "release-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(record["version"], self.version)
        self.assertEqual(record["sha256"], digest)
        self.assertEqual(set(record["includes"]), set(validate_skill.RUNTIME_FILES))
        self.assertEqual(set(record["file_sha256"]), set(validate_skill.RUNTIME_FILES))

    def test_verify_artifacts_accepts_freshly_built_release(self):
        archive = self.build()
        digest = packager.verify_artifacts(archive, self.root)
        self.assertEqual(digest, packager.sha256(archive.read_bytes()))

    def test_verify_rejects_tampered_member(self):
        archive = self.build()
        with zipfile.ZipFile(archive) as zipped:
            original = {info.filename: zipped.read(info) for info in zipped.infolist()}
        tampered_payload = dict(original)
        tampered_payload["journal-fit-engine/README.md"] += b"\ntampered\n"
        tampered = self.out_dir / "tampered.zip"
        with zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_STORED) as zipped:
            for name, data in tampered_payload.items():
                zipped.writestr(name, data)
        with self.assertRaises(ValueError):
            packager.verify_archive(tampered, expected=original)

    def test_verify_artifacts_rejects_wrong_filename(self):
        archive = self.build()
        renamed = archive.with_name("journal-fit-engine-v9.9.9.zip")
        archive.rename(renamed)
        with self.assertRaises(ValueError):
            packager.verify_artifacts(renamed, self.root)

    def test_verify_artifacts_rejects_checksum_mismatch(self):
        archive = self.build()
        sidecar = archive.with_suffix(".zip.sha256")
        sidecar.write_text(
            f"0000000000000000000000000000000000000000000000000000000000000000  {archive.name}\n",
            encoding="utf-8")
        with self.assertRaises(ValueError):
            packager.verify_artifacts(archive, self.root)

    def test_verify_artifacts_rejects_manifest_mismatch(self):
        archive = self.build()
        manifest_path = self.out_dir / "release-manifest.json"
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        record["version"] = "9.9.9"
        manifest_path.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(ValueError):
            packager.verify_artifacts(archive, self.root)

    def test_build_rejects_version_mismatch_argument(self):
        with self.assertRaises(ValueError):
            packager.build(self.root, self.out_dir, version="9.9.9")

    def test_build_fails_closed_on_invalid_source(self):
        (self.root / "references/fit-model.md").unlink()
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse(self.archive_path().exists())

    def test_release_version_rejects_malformed_version(self):
        (self.root / "VERSION").write_text("v0.1.0", encoding="utf-8")
        with self.assertRaises(ValueError):
            packager.release_version(self.root)

    def test_cli_build_then_verify_round_trip(self):
        build = subprocess.run(
            [sys.executable, str(SCRIPTS / "package_runtime.py"),
             "--root", str(self.root), "--out-dir", str(self.out_dir)],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        self.assertIn("PASS:", build.stdout)
        verify = subprocess.run(
            [sys.executable, str(SCRIPTS / "package_runtime.py"),
             "--root", str(self.root), "--verify", str(self.archive_path())],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        self.assertIn("PASS:", verify.stdout)

    def test_cli_reports_failure_without_traceback(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "package_runtime.py"),
             "--root", str(self.root), "--verify", str(self.out_dir / "missing.zip")],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL:", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
