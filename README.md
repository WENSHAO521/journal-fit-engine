# Journal Fit Engine

Cross-disciplinary evidence-aware journal matching, submission strategy, and
manuscript–venue fit — an Agent Skill. Repository version: **v0.2.0**
(working state — see [GitHub Releases](https://github.com/WENSHAO521/journal-fit-engine/releases)
for what is actually published).

> Its objective is not "find the journal with the highest metric." It is
> "find the strongest scholarly conversation in which this manuscript can
> plausibly make its contribution."

## What it does

Journal Fit Engine profiles a manuscript's discipline, contribution,
methodology, genre, and audience; discovers and filters realistic candidate
journals; verifies current journal evidence (scope, article types, APC,
indexing, integrity); and produces explainable, evidence-backed venue
shortlists, gap analyses, and sequential submission strategies — without
pretending to predict acceptance.

It explicitly does **not** function as: a journal-name generator, an
impact-factor sorter, a prestige-ranking tool, an acceptance predictor, a
pay-to-publish recommender, a generic "top 10 journals" list, or an
APC-driven recommendation engine.

## Why manuscript–journal fit, not journal prestige

Journals exist as scholarly conversations, not just rankings. A manuscript
that is topically adjacent to a prestigious journal but methodologically or
generically mismatched will likely be desk-rejected regardless of quality.
Journal Fit Engine recommends venues because the manuscript belongs in their
conversation — matched on intellectual, methodological, disciplinary,
audience, and article-type grounds — not merely because a journal scores
well on an index.

## How matching works

```
Manuscript Profile
      ↓
Contribution & genre classification
      ↓
Candidate generation (10–30 journals; references, neighbor literature,
disciplinary indexes, user-provided targets — never keyword search alone)
      ↓
Hard filters (eliminate incompatible candidates)
      ↓
Soft-fit ranking across multiple dimensions
      ↓
Current-evidence verification + integrity screening
      ↓
Shortlist (3–8 journals) with gap analysis and submission strategy
```

See [SKILL.md](SKILL.md) for the full workflow and
[references/](references/) for the detailed policy on each stage.

## Manuscript Profile

Captures discipline, subdiscipline, topic, research question, central and
secondary contribution, theoretical framework, research design, methods,
data, unit of analysis, geographic/temporal scope, article type, audience,
interdisciplinarity, policy/clinical relevance, technical depth, word count,
reference count, and current stage. Unknown fields stay unknown — nothing is
invented. See [references/manuscript-profile.md](references/manuscript-profile.md).

## Journal Profile

Captures journal identity (title, publisher, ISSN/eISSN), scope, audience,
accepted article types, word limits, abstract requirements, reference style,
OA model, APC, indexing, submission URL, and official guidelines —
distinguishing **OFFICIAL JOURNAL DATA** from **OBSERVED ARTICLE PROFILE**
(recurring topics, dominant methods, typical structure) at every point. See
[references/journal-profile.md](references/journal-profile.md).

## Fit dimensions

scope, topic, theory, method, article-type, audience, contribution,
disciplinary, interdisciplinary, regional, writing-architecture,
submission-constraint, and career-strategy fit — weighted differently by
manuscript type (e.g. method fit dominates for empirical social science;
argument-tradition dominates for philosophy; study design dominates for
clinical medicine; subject classification dominates for mathematics). See
[references/fit-model.md](references/fit-model.md) and the per-family
breakdowns in [disciplines/](disciplines/).

## Hard filters

Article type not accepted, word limit fundamentally incompatible, journal
inactive/discontinued, unsupported language, or explicit out-of-scope
statement eliminate a candidate outright. Everything else (topic strength,
method prevalence, theory orientation, audience, writing style) is soft fit —
it ranks, it does not eliminate. See [references/fit-model.md](references/fit-model.md).

## Candidate discovery

Candidates come from the manuscript's own references, recent literature
closest in question/method/theory/data, disciplinary indexes, author
publication history, related-paper venues, and user-provided targets — never
from keyword search alone. See [references/candidate-generation.md](references/candidate-generation.md).

## Evidence policy

A tiered hierarchy — official journal/publisher pages, then trusted
scholarly indexes, then recent published articles, then secondary listings —
governs what can be trusted for which kind of claim. Confidence in each
recommendation is tagged `HIGH_EVIDENCE`, `MODERATE_EVIDENCE`, or
`LIMITED_EVIDENCE`, and every candidate carries a provenance record of what
was actually checked. See [references/evidence-policy.md](references/evidence-policy.md).

## Current journal data

Scope, APC, indexing, submission rules, and article types drift over time.
When current data can't be verified, the engine outputs
`CURRENT_STATUS_NOT_VERIFIED` rather than inventing a plausible-sounding
fact, and journal profiles are tagged `CURRENT`/`AGING`/`STALE`/`INCOMPLETE`
with refresh triggers. See [references/journal-profile.md](references/journal-profile.md)
and [references/evidence-policy.md](references/evidence-policy.md).

## Submission strategy

A two-stage model — intellectual fit first, strategic factors (indexing,
APC, prestige, timing) second — feeds a tiered submission ladder (ambitious /
strong realistic / conservative fallback), explicit `STRETCH` labeling with
concrete strengthening steps, per-candidate gap analysis, submission-readiness
states, and constraint-relaxation handling when no candidate satisfies every
requirement. See [references/submission-strategy.md](references/submission-strategy.md).

## APC, open access, and indexing

APC is reported with its verification date and distinguished from hybrid OA
charges and diamond OA; a stated no-APC constraint is treated as a hard
constraint. Indexing (SSCI/SCIE/Scopus/etc.) and quartile claims are
verified against the index's own listing where possible, with the specific
ranking system and category always named. See
[references/apc-open-access.md](references/apc-open-access.md) and
[references/indexing-metrics.md](references/indexing-metrics.md).

## Journal integrity

Every recommendation includes a publication-integrity check (publisher
identity, editorial transparency, peer-review description, archiving, ISSN
validity, indexing claims, contact transparency, ethics policy) and
discontinuation-status detection (ceased/discontinued/renamed/merged/
inactive). Uncertain evidence is labeled `LOW INTEGRITY CONFIDENCE`,
`NEEDS VERIFICATION`, or `SIGNIFICANT TRANSPARENCY CONCERNS` rather than an
unsupported "predatory" verdict. See
[references/journal-integrity.md](references/journal-integrity.md).

## Integration

Fits into a four-layer architecture: Adaptive Model Router (execution
strategy) → Scholarly Corpus Builder (evidence acquisition) → Scholarly
Voice Engine (manuscript writing/argument) → Journal Fit Engine (venue
selection, this Skill). It requests only missing evidence from the Corpus
Builder and hands compact adaptation targets to the Voice Engine — it does
not perform retrieval or rewriting itself, and also runs standalone when
those peers aren't present. See [references/integration.md](references/integration.md).

## Reference implementation (`jfe/`)

A real, tested, live-verified Python package operationalizing the
mechanical parts of the workflow above -- not a replacement for the LLM's
own reasoning on soft fit, candidate generation, integrity screening, or
submission strategy (see SKILL.md §Reference implementation for the exact
boundary):

- `jfe.journal_evidence` — live lookup via OpenAlex Sources (primary: APC,
  OA/DOAJ status, topics, activity years) with Crossref Journals as a
  fallback. Keeps identity/APC fields (`OFFICIAL_REQUIREMENTS`-adjacent)
  and activity/topic fields (`OBSERVED_CORPUS_PROFILE`-adjacent) in
  separate dataclass fields, never blurred.
- `jfe.apc_oa` — classifies `MANDATORY_APC` / `DIAMOND_OA` /
  `HYBRID_OA_OPTIONAL` / `UNKNOWN` from OpenAlex's `is_oa`/`apc_usd`/
  `is_in_doaj` fields; a stated `no_mandatory_apc` constraint is violated
  only by `MANDATORY_APC`, never by an optional hybrid fee.
- `jfe.hard_filters` — journal-inactivity (no indexed output in 4+ years),
  no-mandatory-APC-constraint, and honest `CANNOT_VERIFY` results (never a
  fabricated pass) for article-type/language policy that neither index
  exposes at the source level. `CANNOT_VERIFY` alone never eliminates a
  candidate.
- `jfe.fit_model` — one soft-fit dimension implemented so far: topic
  overlap between the manuscript's keyword bag and the journal's indexed
  topics, mapped to the six categorical labels (never a numeric score
  returned to the caller).
- `jfe.manuscript_profile` — `MANUSCRIPT_PROFILE_V1` shape validation.

```bash
python -m jfe.cli lookup-journal --query "Journal of Public Administration Research and Theory"
python -m jfe.cli evaluate-fit --manuscript-json manuscript.json --query "..."
```

Not yet implemented in code (tracked in CHANGELOG, still handled by the
LLM's own reasoning per SKILL.md): candidate generation/discovery,
journal-integrity screening, indexing/quartile verification beyond what
OpenAlex/Crossref expose, submission-strategy ladders, and every soft-fit
dimension besides topic overlap (method, theory, audience, article-type,
regional, writing-architecture).

## Evaluation, testing, and packaging

54 test cases across `evals/manuscript-profile.jsonl`,
`evals/hard-filter.jsonl`, `evals/fit-ranking.jsonl`,
`evals/current-data.jsonl`, `evals/integrity-cases.jsonl`, and
`evals/strategy-cases.jsonl`, covering manuscript profiling, hard exclusion,
method/article-type/audience fit, current-data and APC/indexing uncertainty,
regional and interdisciplinary matching, stretch-vs-realistic distinctions,
integrity screening, and known anti-patterns (impact-factor-only ranking,
keyword-only matching, inactive-journal recommendation, no-APC constraint
violation, pay-to-publish framing). These are policy fixtures the validator
checks for schema consistency; they are not a live model-quality benchmark.

From the repository root (Python 3.11+, standard library only, no
third-party dependencies):

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -v
git diff --check
python scripts/package_runtime.py
python scripts/package_runtime.py --verify dist/journal-fit-engine-v0.2.0.zip
```

`scripts/validate_skill.py` checks required structure, frontmatter, local
Markdown links, JSONL eval schema, the eval-count minimum, and VERSION/
CHANGELOG consistency. `scripts/package_runtime.py` builds a deterministic
33-file runtime ZIP (`SKILL.md`, `README.md`, `LICENSE`, `agents/openai.yaml`,
all of `references/`, `disciplines/`, and `jfe/` — excluding CHANGELOG,
VERSION, evals, scripts, and tests) with a SHA-256 checksum and a generated
`release-manifest.json`, then re-validates the extracted contents.
[GitHub Actions](.github/workflows/validate.yml) runs all three on every
push and pull request. See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for
the manual publish-after-CI procedure.

## Limitations

- No acceptance guarantee, explicit or implied.
- `jfe.journal_evidence` looks up one named/ISSN-identified journal at a
  time against OpenAlex/Crossref; it is not a candidate-generation or
  discovery engine, and there is no exhaustive global journal database —
  candidate discovery is still an LLM-reasoning task per SKILL.md, not
  implemented in code.
- Indexing/quartile verification (SSCI/SCIE/Scopus/DOAJ beyond OpenAlex's
  own `is_in_doaj` flag) is not implemented in code; indexing claims
  beyond that are still an LLM-reasoning task, verified when possible and
  marked unverified otherwise.
- `jfe.fit_model` implements exactly one soft-fit dimension (topic
  overlap via OpenAlex's indexed topics) as real, tested code; method,
  theory, audience, article-type, regional, and writing-architecture fit
  remain LLM-reasoning tasks per `references/fit-model.md`, not code.
- `jfe.hard_filters`' language and article-type checks honestly return
  `CANNOT_VERIFY` — neither OpenAlex nor Crossref exposes a journal's
  accepted-language or accepted-article-type list at the source level.
- Observed publishing patterns are not the same as formal editorial policy —
  they describe recent tendencies, not binding rules.
- Stylistic or structural similarity to a journal's back catalog does not
  predict acceptance.
- APC, review-time, and acceptance-rate figures are not guaranteed stable —
  live-verified 2026-09-09 (see CHANGELOG and the manual
  [live-check workflow](.github/workflows/live-check.yml)), not a
  permanent guarantee; always verify against the current official source
  before submitting.
- Journal-integrity screening (`references/journal-integrity.md`) and
  submission-strategy ladders (`references/submission-strategy.md`) remain
  LLM-reasoning tasks, not implemented in code.

## Installation

Copy the `journal-fit-engine/` directory into your Agent Skills directory
(or reference it as a standalone Skill repository). No external package
dependencies are required; `scripts/validate_skill.py` uses only the Python
standard library.
