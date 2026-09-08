# Journal Fit Engine

Cross-disciplinary evidence-aware journal matching, submission strategy, and
manuscript–venue fit — an Agent Skill.

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

## Evaluation

54 test cases across `evals/manuscript-profile.jsonl`,
`evals/hard-filter.jsonl`, `evals/fit-ranking.jsonl`,
`evals/current-data.jsonl`, `evals/integrity-cases.jsonl`, and
`evals/strategy-cases.jsonl`, covering manuscript profiling, hard exclusion,
method/article-type/audience fit, current-data and APC/indexing uncertainty,
regional and interdisciplinary matching, stretch-vs-realistic distinctions,
integrity screening, and known anti-patterns (impact-factor-only ranking,
keyword-only matching, inactive-journal recommendation, no-APC constraint
violation, pay-to-publish framing). Run `python scripts/validate_skill.py`
to validate repository structure, frontmatter, links, and eval-file schema
(standard library only, no dependencies).

## Limitations

- No acceptance guarantee, explicit or implied.
- No exhaustive global journal database — candidate discovery is targeted,
  not comprehensive.
- No guaranteed real-time access to indexing databases; indexing claims are
  verified when possible and marked unverified otherwise.
- Observed publishing patterns are not the same as formal editorial policy —
  they describe recent tendencies, not binding rules.
- Stylistic or structural similarity to a journal's back catalog does not
  predict acceptance.
- APC, review-time, and acceptance-rate figures are not guaranteed stable —
  always verify against the current official source before submitting.

## Installation

Copy the `journal-fit-engine/` directory into your Agent Skills directory
(or reference it as a standalone Skill repository). No external package
dependencies are required; `scripts/validate_skill.py` uses only the Python
standard library.
