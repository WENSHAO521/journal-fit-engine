# Changelog

All notable changes to Journal Fit Engine are documented in this file.

## [0.2.0] — 2026-09-09

First real, tested, live-verified implementation of the mechanical parts
of the workflow -- `jfe/`, a standard-library-only Python package. Before
this release the entire fit engine was prose (SKILL.md + references) with
no working code; v0.1.0's own roadmap called this "v0.3 -- live indexing/
APC/author-guideline refresh," delivered here ahead of schedule for the
APC/OA and evidence-lookup portions. Candidate generation, journal-
integrity screening, most soft-fit dimensions, and submission-strategy
ladders are still LLM-reasoning tasks per SKILL.md, not code -- see
"Still not implemented" below.

### Added

- `jfe.http_client` — minimal dependency-free HTTP client with an
  injectable transport (tests never touch the network) and bounded
  429/5xx retry.
- `jfe.manuscript_profile` — `MANUSCRIPT_PROFILE_V1` shape validation and
  a stopword-filtered keyword extractor used by the fit model.
- `jfe.journal_evidence` — live journal evidence lookup via OpenAlex
  Sources (primary) with Crossref Journals fallback. Keeps identity/APC
  fields separate from activity/topic fields per SKILL.md's Evidence
  discipline; every result carries a `provenance_note` stating it is
  index-sourced, not the journal's own official page.
- `jfe.apc_oa` — classifies `MANDATORY_APC` / `DIAMOND_OA` /
  `HYBRID_OA_OPTIONAL` / `UNKNOWN`; a `no_mandatory_apc` constraint is
  violated only by `MANDATORY_APC`, never an optional hybrid fee or
  absence of evidence.
- `jfe.hard_filters` — journal-inactivity check (4+ years with no indexed
  output), no-mandatory-APC-constraint check, and honest `CANNOT_VERIFY`
  for article-type/language policy that no available index exposes.
  `CANNOT_VERIFY` alone never eliminates a candidate; only an actual
  `FAIL` does.
- `jfe.fit_model` — one soft-fit dimension (topic overlap between the
  manuscript's keyword bag and the journal's indexed topics) mapped to
  the six categorical labels from SKILL.md's no-fake-precision rule; the
  internal numeric score used for ranking is never returned to the
  caller.
- `jfe.cli` — `lookup-journal` and `evaluate-fit` developer commands.
- 35 new tests (fully offline, injected-transport for network paths) plus
  a manual-only `.github/workflows/live-check.yml` smoke test against the
  real OpenAlex/Crossref APIs (never gates CI or releases).
- `jfe/` added to the runtime ZIP allowlist (33 files, was 25) and to
  `scripts/validate_skill.py`'s required-files check.

### Fixed (found via live verification against real journals, not assumed)

- An early version of `jfe.fit_model`'s topic-overlap matcher counted
  common connector words ("and", "for", ...) as matched evidence because
  they pass a length>2 filter and appear in both manuscript text and real
  OpenAlex topic names (e.g. "Public Policy **and** Administration
  Research"). A stopword list now excludes them from both the manuscript
  keyword bag and the journal topic-word set.
- `jfe.journal_evidence`'s Crossref adapter assumed `ISSN` entries were
  `{"value": ...}` objects (true for some Crossref endpoints); the actual
  Journals API returns a flat list of ISSN strings, which crashed the
  adapter on first live use. Fixed to match the real response shape.

### Verified live (2026-09-09, not a permanent guarantee)

- `lookup_by_name`/`lookup_by_issn` against OpenAlex Sources for a real
  journal (Journal of Public Administration Research and Theory: correct
  ISSN, publisher, APC of $4029, 25 real topic names).
- `apc_oa.classify` against a real gold-OA journal (PLOS ONE: correctly
  classified `MANDATORY_APC` at $2382).
- `evaluate-fit` end-to-end: a matching manuscript scored `STRONG FIT`
  with named overlapping topics; a genuinely unrelated manuscript (quantum
  computing vs. a public-administration journal) correctly scored
  `NOT RECOMMENDED` with zero fabricated overlap; a manuscript with a
  `no_mandatory_apc` constraint was correctly hard-eliminated against
  PLOS ONE's real mandatory APC.

### Still not implemented (honest, not smoothed over)

- Candidate generation/discovery (references/candidate-generation.md) —
  still entirely an LLM-reasoning task.
- Journal-integrity screening (references/journal-integrity.md).
- Indexing/quartile verification beyond OpenAlex's own `is_in_doaj` flag
  (no SSCI/SCIE/Scopus/MEDLINE/PubMed adapter).
- Every soft-fit dimension except topic overlap: method, theory, article-
  type, audience, regional, writing-architecture, submission-constraint,
  career-strategy fit.
- Submission-strategy ladders (references/submission-strategy.md).
- Scholarly Corpus Builder integration (still the v0.1.0 roadmap's
  original "v0.2" item, now deferred -- see Roadmap below).

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

- ~~v0.2 — Live indexing/APC/author-guideline refresh~~ — done in v0.2.0
  for APC/OA and evidence lookup; author-guideline scraping and indexing
  beyond `is_in_doaj` remain open.
- **v0.3** — Candidate generation/discovery in code (currently
  LLM-reasoning only).
- **v0.4** — Remaining soft-fit dimensions in code (method, theory,
  article-type, audience) beyond the v0.2.0 topic-overlap dimension.
- **v0.5** — Scholarly Corpus Builder integration and cached
  journal-profile reuse (the original v0.1.0 roadmap's "v0.2" item,
  deferred here since live-evidence lookup didn't require it).
- **v0.6** — Journal-integrity screening and submission-ladder logic in
  code.
- **v1.0** — Only after real candidate discovery, hard filters, current-
  evidence lookup, and protocol validation all work together end-to-end
  with cross-disciplinary evidence, per this Skill's own acceptance
  criteria -- not claimed by any version bump alone.
