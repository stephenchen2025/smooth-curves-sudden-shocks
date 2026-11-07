# Attention vs. capability: analysis code

Tests whether frontier AI capability moves smoothly while public attention and policy
move in steps (H1–H4 in the study design doc).

## Contents

| File | What it does | Runs without internet? |
| --- | --- | --- |
| `capability.py` | Refits METR time horizons per model from run-level data (METR's headline method) | Yes, after cloning METR's repo |
| `breaks.py` | A1 / H1: prediction test, Chow-style break test and placebo scan at the shock dates | Yes |
| `attention.py` | Collectors for Wikipedia pageviews and Google Trends, a BigQuery query for GDELT, and the weekly attention index | No (collectors need network) |
| `analyze.py` | A2–A4 / H2–H4: local projections, Poisson local projections, decay; permutation tests; `--simulate` self-test | Yes |
| `data/events_seed.csv` | 17 policy and 5 visibility events, 2022–2026, each with a source link | — |
| `out/` | Results already produced from METR's public data | — |

## Setup

```bash
pip install -r requirements.txt
git clone --depth 1 https://github.com/METR/eval-analysis-public.git ../metr
```

## 1. Capability side (already run; reproduces `out/`)

```bash
python capability.py --repo ../metr --version 1-0 --out out/horizons_1-0.csv
python capability.py --repo ../metr --version 1-1 --out out/horizons_1-1.csv
python breaks.py --horizons out/horizons_1-0.csv --label "TH 1.0" --out out/breaks_1-0.csv
python breaks.py --horizons out/horizons_1-1.csv --label "TH 1.1" --out out/breaks_1-1.csv
```

## 2. Attention side (run on your machine)

One command collects Wikipedia (API), GDELT (free DOC API, no account) and Google Trends, checks the
Wikipedia pull against the Hugging Face copy used in the first run, and runs A2–A4 into `out/attention_full/`:

```bash
./run_local.sh
```

It takes 30–60 minutes, mostly Google Trends back-off, and skips any series already collected if you
re-run it. A failed source is skipped and the analysis runs on the rest. The full run's rules were
pre-registered in `data/FREEZE.md` (addendum) before any Trends or GDELT data existed.

The collectors were not run from the environment they were written in (no network there). Things that may need a tweak:
- GDELT DOC returns daily points for 6-month windows; if it returns coarser steps, lower `chunk_months`;
- Google Trends window stitching if a window returns all zeros;
- the BigQuery route (`attention.py gdelt-sql`) remains as an alternative; dry-run it first, since GKG is large.

Congress.gov: run an advanced search for bills mentioning "artificial intelligence", export CSV,
and convert to the long format `date,series,value` (one row per introduction date, value 1).

## 3. Events

Extend `data/events_seed.csv` using the coding manual in the design doc, then freeze it
(pre-register) before looking at the attention series. Save as `data/events.csv`.

## 3b. First attention run (Nov 7, 2026): Wikipedia only

The workspace could not reach the Wikimedia API, so the pageviews came from a CC0 copy on
Hugging Face (`itsalissonsilva/wikimedia-pageviews-forecasting`), saved window by window in
`data/hf_rows/` and stitched with `scripts/stitch_rows.py` (all overlapping days agree).
`data/FREEZE.md` records the hashes of the event list and `analyze.py`, frozen before the AI series was opened.

```bash
python scripts/stitch_rows.py data/hf_rows data/wiki_hf.csv
python scripts/run_attention.py          # main spec + robustness grid -> out/attention/ (about 4 min)
python scripts/exploratory_seasonal.py   # exploratory checks, not pre-registered
```

To confirm the mirrored data, run `python attention.py wikipedia --out data/wiki.csv` on your machine
and compare the overlapping days with `data/wiki_hf.csv`.

## 4. Analysis

```bash
python analyze.py --simulate     # sanity check: recovers planted effects (about 30 s)
python analyze.py --attention data/attention_index.csv --events data/events.csv \
    --horizons out/horizons_1-0.csv out/horizons_1-1.csv --out out/
```

Outputs: `a2_attention_lp.csv`, `a3_policy_lp.csv`, `a4_decay.csv`, `a2_permutation_p.csv`.
