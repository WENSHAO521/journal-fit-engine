#!/usr/bin/env python3
"""
validate_skill.py — standard-library-only validator for the journal-fit-engine
Agent Skill repository.

Checks:
  - required top-level files exist
  - SKILL.md has valid frontmatter with name + description
  - all references/*.md and disciplines/*.md files listed in the architecture exist
  - agents/openai.yaml exists and contains name/description keys
  - all local markdown links inside SKILL.md, references/*.md, disciplines/*.md
    resolve to files that actually exist
  - evals/*.jsonl files are valid JSONL, have unique ids (per file and globally),
    and each record has the required eval fields
  - at least 50 total eval cases across the evals/ directory

Exit code 0 = all checks passed. Exit code 1 = at least one check failed.
No third-party dependencies.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_TOP_FILES = ["SKILL.md", "README.md", "CHANGELOG.md", "LICENSE"]

REQUIRED_REFERENCES = [
    "manuscript-profile.md",
    "journal-profile.md",
    "fit-model.md",
    "candidate-generation.md",
    "evidence-policy.md",
    "journal-integrity.md",
    "submission-strategy.md",
    "indexing-metrics.md",
    "apc-open-access.md",
    "adaptation-policy.md",
    "integration.md",
]

REQUIRED_DISCIPLINES = [
    "natural-sciences.md",
    "mathematics.md",
    "engineering-computing.md",
    "medicine-health.md",
    "social-sciences.md",
    "management.md",
    "law.md",
    "humanities.md",
    "education.md",
    "interdisciplinary.md",
]

REQUIRED_EVAL_FILES = [
    "manuscript-profile.jsonl",
    "hard-filter.jsonl",
    "fit-ranking.jsonl",
    "current-data.jsonl",
    "integrity-cases.jsonl",
    "strategy-cases.jsonl",
]

REQUIRED_EVAL_FIELDS = ["id", "category", "discipline", "scenario", "expected_behavior"]

MIN_TOTAL_EVAL_CASES = 50

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def check_required_files():
    for name in REQUIRED_TOP_FILES:
        if not (ROOT / name).is_file():
            fail(f"Missing required top-level file: {name}")

    if not (ROOT / "agents" / "openai.yaml").is_file():
        fail("Missing agents/openai.yaml")

    for name in REQUIRED_REFERENCES:
        if not (ROOT / "references" / name).is_file():
            fail(f"Missing required reference file: references/{name}")

    for name in REQUIRED_DISCIPLINES:
        if not (ROOT / "disciplines" / name).is_file():
            fail(f"Missing required discipline file: disciplines/{name}")

    for name in REQUIRED_EVAL_FILES:
        if not (ROOT / "evals" / name).is_file():
            fail(f"Missing required eval file: evals/{name}")

    if not (ROOT / "scripts" / "validate_skill.py").is_file():
        fail("Missing scripts/validate_skill.py (this file)")


def parse_frontmatter(text):
    """Return dict of simple key: value frontmatter fields from a --- block."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    block = m.group(1)
    fields = {}
    for line in block.splitlines():
        kv = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if kv:
            fields[kv.group(1)] = kv.group(2).strip()
    return fields


def check_skill_frontmatter():
    skill_path = ROOT / "SKILL.md"
    if not skill_path.is_file():
        return
    text = skill_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if fm is None:
        fail("SKILL.md is missing a --- frontmatter block")
        return
    if fm.get("name") != "journal-fit-engine":
        fail(f"SKILL.md frontmatter 'name' should be 'journal-fit-engine', got: {fm.get('name')!r}")
    if not fm.get("description"):
        fail("SKILL.md frontmatter is missing a non-empty 'description'")


def check_agents_yaml():
    path = ROOT / "agents" / "openai.yaml"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if not re.search(r"^name:\s*\S+", text, re.MULTILINE):
        fail("agents/openai.yaml missing top-level 'name:' key")
    if "description:" not in text:
        fail("agents/openai.yaml missing top-level 'description:' key")


LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def check_local_links():
    md_files = []
    for sub in ["", "references", "disciplines"]:
        base = ROOT / sub if sub else ROOT
        if base.is_dir():
            md_files.extend(sorted(base.glob("*.md")))

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            target_path_part = target.split("#", 1)[0]
            if not target_path_part:
                continue
            resolved = (md_file.parent / target_path_part).resolve()
            if not (resolved.is_file() or resolved.is_dir()):
                fail(f"Broken local link in {md_file.relative_to(ROOT)}: '{target}' -> {resolved} does not exist")


def check_evals():
    all_ids_global = {}
    total_cases = 0

    for name in REQUIRED_EVAL_FILES:
        path = ROOT / "evals" / name
        if not path.is_file():
            continue
        ids_in_file = set()
        with path.open(encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    fail(f"evals/{name}:{lineno} invalid JSON: {e}")
                    continue

                total_cases += 1

                missing = [field for field in REQUIRED_EVAL_FIELDS if field not in record]
                if missing:
                    fail(f"evals/{name}:{lineno} record missing required fields: {missing}")

                if not isinstance(record.get("expected_behavior"), list) or not record.get("expected_behavior"):
                    fail(f"evals/{name}:{lineno} 'expected_behavior' must be a non-empty list")

                rec_id = record.get("id")
                if rec_id:
                    if rec_id in ids_in_file:
                        fail(f"evals/{name}:{lineno} duplicate id within file: {rec_id}")
                    ids_in_file.add(rec_id)

                    if rec_id in all_ids_global:
                        fail(
                            f"evals/{name}:{lineno} duplicate id across files: {rec_id} "
                            f"(also in {all_ids_global[rec_id]})"
                        )
                    else:
                        all_ids_global[rec_id] = name

    if total_cases < MIN_TOTAL_EVAL_CASES:
        fail(f"Total eval cases ({total_cases}) is below required minimum ({MIN_TOTAL_EVAL_CASES})")
    else:
        warn(f"Total eval cases: {total_cases} (minimum required: {MIN_TOTAL_EVAL_CASES})")


def check_profile_schema_examples():
    manuscript_profile = ROOT / "references" / "manuscript-profile.md"
    journal_profile = ROOT / "references" / "journal-profile.md"

    if manuscript_profile.is_file():
        text = manuscript_profile.read_text(encoding="utf-8")
        if "discipline:" not in text or "contribution_type:" not in text:
            fail("references/manuscript-profile.md does not appear to contain the manuscript profile schema")

    if journal_profile.is_file():
        text = journal_profile.read_text(encoding="utf-8")
        if "issn:" not in text or "article_types:" not in text:
            fail("references/journal-profile.md does not appear to contain the journal profile schema")


def main():
    check_required_files()
    check_skill_frontmatter()
    check_agents_yaml()
    check_local_links()
    check_evals()
    check_profile_schema_examples()

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"FAILED: {len(errors)} error(s) found:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: all validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
