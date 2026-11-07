# Handoff: state of the project (November 7, 2026)

Read this first if you are picking the work up in a new session.

## What the project is

An arXiv paper, *Smooth Curves, Sudden Shocks: Governing Incremental AI Progress in an Age of
Step-Change Perception*. Its claim is that frontier AI capability grows along smooth, measurable
curves, while public attention and policy move in steps set off by visible events. Governance
should therefore be indexed to measured capability rather than to shocks. The paper started as an
essay and now has two original analyses:

1. **Capability break tests (done).** METR time horizons are refitted from run-level data, and
   trend breaks are tested at the shock dates (ChatGPT, DeepSeek-R1, July 2026 Hugging Face intrusion).
2. **Pre-registered attention study (half done).** This is a weekly test of whether attention and
   policy follow visibility rather than capability (H2–H4). Only a Wikipedia-only pilot has run so far.

## Where things are

| Path | What |
| --- | --- |
| `paper/smooth-curves-sudden-shocks.{pdf,docx,md}` | The paper. The Markdown export has placeholders where the four figures are; the figures are in the PDF |
| `study-design/study-design.{pdf,docx,md}` | Study design, coding manual, and results so far (§5 capability, §6 attention pilot) |
| `study/` | All code and data; see `study/README.md` for the commands |
| `study/data/events.csv` | **Frozen** event list: 43 policy and 20 visibility events, 2021-04 to 2026-09, one source each |
| `study/data/FREEZE.md` | Pre-registration record with SHA-256 hashes, plus an addendum fixing the rules for the full run |
| `study/out/` | Capability outputs (`horizons_*.csv`, `breaks_*.csv`, `placebo_*.csv`) and `attention/` (pilot) |

The live, editable versions are Claude Docs owned by the author:
paper https://claude.ai/artifact/84Nt2swSF5hSUemUyMiDyu and study design
https://claude.ai/artifact/9sjLmUh8GcMxrruZzam5pn. The files here are exports from November 7, 2026.
If you edit the paper here, tell the author which version is current.

## Results so far

**Capability (paper §3.2, study §5).** The refits reproduce METR's published horizons: log horizons
correlate at 0.999 across 48 model–suite pairs, with a median gap of 0.06 doublings. Doubling times
are 6.8 months for Time Horizon 1.0 (95% CI 6.1–7.8) and 4.1 months for 1.1 (3.6–4.7). No break is
specific to the DeepSeek-R1 date: break-test p = 0.02–0.05, but 36–75% of placebo months give a
statistic at least as large. The ChatGPT date cannot be tested, because only three models precede
it; GPT-4 landed about 0.8 doublings above the full trend. The July 2026 intrusion cannot be tested
yet, because METR's public runs end with February 2026 releases.

**Attention pilot (paper §4.5, study §6).** This used Wikipedia pageviews for the Artificial
intelligence and Machine learning articles, 299 weeks from 2021 to 2026. Every pre-registered test
is null:

| Test (sum over weeks 0–4) | Estimate | Permutation p |
| --- | --- | --- |
| A2: attention after visibility events | +0.33 SD | 0.50 |
| A2: attention after capability milestones | −0.19 SD | 0.70 |
| A3: policy events on attention changes | +1.20 | 0.18 |
| A3: policy events on capability surprise | +0.74 | 0.86 |
| A4: excess policy after 6 spikes | negative, unstable | 0.76 |

The null is uninformative, because Wikipedia barely registers the ChatGPT launch (it ranks 80th of
298 weekly rises), and the school calendar explains 30% of weekly changes. An exploratory variant
that adds the Large_language_model article gives p = 0.09 for visibility events; that is not
pre-registered. Do not cite the pilot as support for H2–H4.

## Next steps, in order

1. **Collect Google Trends and GDELT, then run the full test.** On a machine with open internet:
   `cd study && ./run_local.sh`. It takes 30–60 minutes and writes `out/attention_full/summary.json`.
   The collectors (`attention.py wikipedia|gdelt-doc|trends`) have **never run against the live
   APIs**, because the session that wrote them had no network access, so expect small fixes. Likely
   spots: the GDELT DOC timeline resolution (`chunk_months`), the Trends window stitching, and
   pytrends rate limits. `scripts/compare_wiki.py` checks the mirrored Wikipedia data against the
   API.
2. **Write up the full results** in the paper (§4.5, abstract, §8.6, conclusion) and in study §6.
   Report the pre-registered specification first; label anything else as exploratory.
3. **Have a second coder check about 20% of the events** and report Cohen's κ. The events were
   coded by Claude from web sources, and the paper discloses this.
4. **Author verification before submission.** The AI-use statement says the author checked the
   analyses, sources and references, so this has to actually happen. Pay particular attention to
   the 2026 case facts (§4.3, §6, §7): some rest on secondary summaries (CASRAI; the Wikipedia page
   on the OpenAI–Hugging Face incident).
5. **Rewrite the introduction and discussion in the author's own voice.**
6. **Submit to arXiv in cs.CY** as an empirical paper, not a position paper. Keep the AI-use
   disclosure, and attach `study/` as supplementary code.
7. Optional: add a congress.gov bill series; re-run A1 when METR publishes runs for models released
   after February 2026; repeat A1 on Epoch's capability index.

## Rules to keep

- Do not edit `study/data/events.csv` or `study/analyze.py`; their hashes are recorded in `FREEZE.md`.
  If either must change after attention data has been seen, add a dated note to `FREEZE.md` and
  treat the affected results as exploratory.
- The full-run rules are in the FREEZE.md addendum. Sample: weeks ending 2021-01-11 to 2026-09-28.
  The main index is the first principal component of the series present in every week; a series
  enters from the first week it reaches 25% of its median weekly value.
- `python study/scripts/run_attention.py` with no arguments reproduces the pilot exactly; use it as a
  regression check after any code change.

## Environment notes from the previous session

That session ran in a sandbox whose outbound network allowed only package registries and GitHub.
Wikimedia, Google Trends, GDELT and BigQuery were unreachable, and no browser was connected. The
pilot pageviews therefore came from a CC0 Hugging Face dataset
(`itsalissonsilva/wikimedia-pageviews-forecasting`), saved window by window in `study/data/hf_rows/`
and stitched with `scripts/stitch_rows.py`. All 652 overlapping days matched. The METR data is not
in this repo; `study/README.md` says how to clone it.
