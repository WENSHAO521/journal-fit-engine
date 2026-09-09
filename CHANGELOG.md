# Changelog

All notable changes to Journal Fit Engine are documented in this file.

## [0.3.0] — 2026-09-09

Closes the `JOURNAL_STYLE_CONTEXT_V1` producer half of the
Journal Fit Engine → Scholarly Voice Engine handoff (previously only a
schema declaration in `scholarly-agent-suite/protocols/`, not emitted by
any code), and expands the fit model from one soft-fit dimension (topic
overlap) to eleven, plus honest integrity and indexing evidence layers.
None of this replaces the LLM-reasoning tasks the SKILL.md workflow still
depends on -- see "Still not implemented" below.

### Added

- `jfe.style_context` — builds and validates a `JOURNAL_STYLE_CONTEXT_V1`
  envelope (`build_journal_style_context()`, `from_journal_evidence()`).
  Structurally enforces the official-requirements/observed-patterns
  separation (SKILL.md §Evidence discipline): a known observed-pattern
  field (e.g. `mean_paragraph_length`) appearing in `official_requirements`
  is rejected, and vice versa -- this is the concrete fix for the gap
  scholarly-voice-engine's own `references/integration.md` flagged as
  "not yet reconciled." Never derives either bucket from this Skill's own
  index evidence (OpenAlex/Crossref are bibliographic indexes, not an
  author-guideline source or corpus sample) -- both must be supplied by
  the caller; an empty bucket produces an explicit `limitations` entry
  instead of silently proceeding. `compute_freshness()` classifies
  `current`/`aging`/`stale` from `JournalEvidence.checked_at` using the
  same 6/12-month windows scholarly-corpus-builder's refresh policy
  already documents, and defaults to `stale` (never a silent `current`)
  when `checked_at` is missing or unparseable.
- `jfe.fit_dimensions` — eleven evidence-backed fit dimensions (scope,
  topic, article-type, method, audience, activity/recency, APC
  constraint, OA model, journal integrity, indexing evidence, requirement
  compatibility), each returning one of
  `MATCH`/`PARTIAL_MATCH`/`WEAK_MATCH`/`MISMATCH`/`CANNOT_VERIFY`/
  `NOT_APPLICABLE` — never a numeric score. A dimension the manuscript
  never asked about (e.g. no stated `article_type`) is honestly
  `NOT_APPLICABLE`; a dimension this Skill's adapters cannot evidence at
  all (e.g. accepted article types, method prevalence, audience) is
  `CANNOT_VERIFY` even when the manuscript did ask — never guessed.
  Supplements, does not replace, `fit_model.compute_fit()`'s single
  overall verdict.
- `jfe.integrity` — journal-integrity screening
  (`VERIFIED`/`WARNING`/`CANNOT_VERIFY` per signal and overall) covering
  identity completeness (ISSN + publisher present), cross-source identity
  consistency (when a second index adapter's evidence is supplied),
  recent activity (reuses `hard_filters.check_inactive`), and APC/OA
  transparency. Deliberately never produces a "predatory probability" or
  a blanket predatory/legitimate verdict -- that judgment call, and the
  editorial-board/peer-review/archiving/COPE-membership evidence it
  actually needs, stays an LLM-reasoning task per
  `references/journal-integrity.md`.
- `jfe.indexing` — indexing/quartile evidence assessment. DOAJ inclusion
  (the one real, free, keyless index this Skill's adapters can check) is
  reported `officially_verified` with source/freshness attached; Scopus,
  Web of Science, SCIE, SSCI, AHCI, ESCI, JCR quartile, CiteScore
  quartile, Impact Factor, and SJR are always `cannot_verify` — never
  inferred from a publisher's claim or from training-data recall of a
  journal's reputation, and never a bare "Q1" without system/category/
  year context (references/indexing-metrics.md).
- `jfe.manuscript_profile.tokenize()` — the stopword-filtered tokenizer
  extracted out of `ManuscriptProfile.keywords()` and `fit_model`'s
  topic-overlap matcher into one shared function, reused by
  `fit_dimensions.scope_fit()` (a real DRY fix made while adding the new
  dimension, not a behavior change to either existing caller).
- `jfe.journal_evidence` now actually populates `checked_at` (was always
  `None` before this release, despite being declared on `JournalEvidence`
  since v0.2.0) -- `lookup_by_name()`/`lookup_by_issn()` stamp it with the
  real UTC time of the successful lookup, which `style_context`'s
  freshness computation depends on.
- `jfe.cli build-style-context` — developer command exercising the new
  producer end to end against live evidence.
- `evaluate-fit` CLI output now also includes `fit_dimensions`,
  `integrity`, and `indexing`.
- 51 new tests (fully offline) covering the four new modules, including
  explicit regression tests for the official/observed contamination rule
  and for freshness never silently defaulting to "current."
- `jfe/` runtime allowlist grew to include the four new modules (12 files,
  was 8) — `scripts/validate_skill.py` and `scripts/package_runtime.py`
  updated accordingly.

### Changed

- `references/integration.md`'s Scholarly Voice Engine section now leads
  with the `JOURNAL_STYLE_CONTEXT_V1` handoff; the older compact/full
  `target_voice_adjustment`/`journal_target` shapes remain valid for a
  caller that has already derived writing-level adjustments and wants to
  skip straight to that.

### Still not implemented (honest, not smoothed over)

- Candidate generation/discovery (references/candidate-generation.md) —
  still entirely an LLM-reasoning task.
- Predatory/legitimate judgment calls, editorial-board/peer-review/
  archiving/COPE-membership evidence — `jfe.integrity` only screens what
  its two free index adapters can actually see (identity completeness,
  cross-source consistency, activity, APC transparency); the fuller
  screen in `references/journal-integrity.md` is still an LLM-reasoning
  task.
- `scope_fit`/`topic_fit` remain bag-of-words overlap, not semantic
  matching; `article_type_fit`/`method_fit`/`audience_fit` are
  `CANNOT_VERIFY` even when the manuscript states the field, because no
  available index exposes a journal's accepted types/method
  prevalence/audience.
- Submission-strategy ladders (references/submission-strategy.md).
- `official_requirements`/`observed_patterns` population itself (fetching
  a journal's real guidelines page; running scholarly-corpus-builder
  against its article sample) is still the caller's job --
  `jfe.style_context` assembles and validates the envelope, it does not
  retrieve either bucket's content.

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
