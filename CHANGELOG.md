# Changelog

All notable changes to Journal Fit Engine are documented in this file.

## [0.1.0] — 2026-09-09

Initial release — core fit engine.

### Added
- `SKILL.md` — compact core workflow: manuscript-first profiling, hard vs.
  soft fit, evidence discipline, no-fake-precision rule, output contract,
  ethical boundaries.
- Manuscript profiling: schema, contribution classification, manuscript
  genre, research-design fit (topic × method × genre), audience fit,
  manuscript fingerprint.
- Journal profiling: schema, official-vs-observed separation, identity
  resolution via ISSN, currency requirements, caching/refresh policy,
  special-issue and journal-transfer handling.
- Fit model: 13 fit dimensions, hard filters vs. soft fit, no-fake-precision
  category labels, per-manuscript-type weighting guidance, theory-fit and
  method/data-fit traps, temporal fit, interdisciplinary fit, geographic/
  internationalization fit, desk-rejection risk signals.
- Candidate generation: discovery pipeline, reference-neighborhood analysis,
  recent-neighbor matching, no-keyword-only-matching rule, Corpus Builder
  reuse.
- Evidence policy: 4-tier evidence hierarchy, current-data requirement,
  current-information failure handling, confidence states, recommendation
  provenance and stability.
- Journal integrity: predatory/integrity screening signals, calibrated
  uncertainty labels, discontinuation/status detection, identity-confusion
  safeguards.
- Submission strategy: two-stage recommendation (intellectual fit, then
  strategic fit), submission ladder, stretch-journal labeling, per-journal
  gap analysis, submission readiness, constraint handling and relaxation,
  recommendation diversity, target-journal audit, reverse journal-fit mode,
  compare-journals mode, no-acceptance-prediction rule.
- Indexing & metrics: SSCI/SCIE/Scopus verification, quartile-system
  precision, impact-metric secondary status, acceptance-rate and
  review-speed reporting rules.
- APC & open access: APC verification, hybrid/diamond/mandatory-fee
  distinctions, no-APC mode handling.
- Adaptation policy: adaptation types, word-count/article-type/abstract/
  reference compatibility, adaptation cost, submission readiness, ethical
  boundaries (no citation padding, no data manipulation, no simultaneous
  submission where prohibited), medicine-specific reporting compliance
  (CONSORT/STROBE/PRISMA/CARE/TRIPOD/STARD/ARRIVE), AI/CS venue-type
  distinctions.
- Integration: contracts with Scholarly Corpus Builder, Scholarly Voice
  Engine, and Adaptive Model Router; standalone-operation fallback.
- Ten discipline reference files covering natural sciences, mathematics,
  engineering/computing, medicine/health, social sciences, management, law,
  humanities (including arts/design), education, and interdisciplinary
  work.
- `agents/openai.yaml` agent metadata.
- 54 eval cases across six JSONL files (manuscript profiling, hard
  exclusion, fit ranking, current-data uncertainty, integrity screening,
  submission strategy), including explicit anti-pattern and ethics-boundary
  cases.
- `scripts/validate_skill.py` — standard-library-only repository validator
  (required files, frontmatter, local links, JSONL schema, eval-count
  minimum, VERSION/CHANGELOG consistency).
- `VERSION` file and CHANGELOG-heading consistency check.
- `tests/test_validate_skill.py` (26 cases) and `tests/test_package_runtime.py`
  (16 cases) — negative-path regression coverage for the validator and
  packager, run against isolated temporary copies of the repository.
- `scripts/package_runtime.py` — deterministic 25-file runtime ZIP with
  SHA-256 checksum and a generated release manifest; excludes CHANGELOG,
  VERSION, evals, scripts, and tests from the bundled runtime.
- `RELEASE_CHECKLIST.md` — manual publish-after-CI release procedure.
- `.github/workflows/validate.yml` — CI running the validator, tests, and
  a packaging dry run on every push/PR.

### Scope for this release
v0.1 ships the core fit engine only: manuscript profiling, journal
profiling, hard filters, fit dimensions, and shortlist generation. Corpus
Builder integration, live indexing/APC refresh, reference-neighborhood
automation, and submission-ladder optimization are designed for but not yet
implemented — see the roadmap in [references/integration.md](references/integration.md)
and the version plan below.

## Roadmap

- **v0.2** — Scholarly Corpus Builder integration and cached journal-profile
  reuse.
- **v0.3** — Live indexing/APC/author-guideline refresh.
- **v0.4** — Automated reference-neighborhood and related-paper venue
  analysis.
- **v0.5** — Submission-ladder optimization and empirical recommendation
  evaluation.
