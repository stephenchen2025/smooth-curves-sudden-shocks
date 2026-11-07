"""Attention series collectors and the weekly attention index.

These collectors need open internet access, so run them on your own machine:

    python attention.py wikipedia --out data/wiki.csv
    python attention.py trends --out data/trends.csv
    python attention.py gdelt-doc --out data/gdelt.csv   # free GDELT DOC API, no account needed
    python attention.py gdelt-sql > gdelt.sql           # alternative: BigQuery (needs a GCP project; costs)
    python attention.py index --inputs data/wiki.csv data/trends.csv data/gdelt.csv --out data/attention_index.csv

Every collector writes a long CSV with columns: date, series, value.
run_local.sh runs all of them and then the analysis.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

START, END = "2019-01-01", "2026-10-31"
USER_AGENT = "attention-capability-study/0.1 (research script)"

WIKI_ARTICLES = ["Artificial_intelligence", "Machine_learning", "ChatGPT", "Large_language_model", "AI_safety"]
# label -> Trends query; "/m/0mkz" is the "Artificial intelligence" topic (all languages and spellings)
TREND_TERMS = {"ai_topic": "/m/0mkz", "ChatGPT": "ChatGPT", "AI agent": "AI agent"}
GDELT_TERMS = ["artificial intelligence", "ChatGPT", "AI agent", "large language model"]
# label -> GDELT DOC query (English-language sources are added below)
GDELT_DOC_QUERIES = {
    "artificial_intelligence": '"artificial intelligence"',
    "chatgpt": "chatgpt",
    "ai_concern": '("ai regulation" OR "ai safety")',
}


# ---------- Wikipedia pageviews (Wikimedia REST API, daily) ----------
def wikipedia(articles=WIKI_ARTICLES, start=START, end=END) -> pd.DataFrame:
    frames = []
    for art in articles:
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
               f"all-access/user/{urllib.parse.quote(art, safe='')}/daily/"
               f"{start.replace('-', '')}00/{end.replace('-', '')}00")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            items = json.load(urllib.request.urlopen(req, timeout=60))["items"]
        except Exception as e:
            print(f"  Wikipedia {art}: {type(e).__name__}; skipped", file=sys.stderr)
            continue
        print(f"  Wikipedia {art}: {len(items)} days", file=sys.stderr)
        frames.append(pd.DataFrame({
            "date": pd.to_datetime([i["timestamp"][:8] for i in items]),
            "series": f"wiki:{art}",
            "value": [i["views"] for i in items],
        }))
        time.sleep(0.5)
    return pd.concat(frames)


# ---------- Google Trends (pytrends, weekly, stitched) ----------
def _trends_window(pytrends, term: str, a: str, b: str, tries: int = 5) -> pd.Series:
    for k in range(tries):
        try:
            pytrends.build_payload([term], timeframe=f"{a} {b}", geo="")
            df = pytrends.interest_over_time()
            return df[term].astype(float)
        except Exception as e:  # usually HTTP 429 (rate limit): back off and retry
            wait = 60 * (k + 1)
            print(f"  Trends {term} {a}..{b}: {type(e).__name__}; retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"Google Trends kept refusing {term} {a}..{b}")


def trends(terms=TREND_TERMS, start=START, end=END, window_years=4, overlap_years=1) -> pd.DataFrame:
    """Google returns weekly data only for windows up to about five years, each rescaled
    to 0-100. We pull overlapping windows and chain them by the median ratio on the overlap."""
    from pytrends.request import TrendReq  # pip install pytrends
    pytrends = TrendReq(hl="en-US", tz=0)
    frames = []
    for label, term in terms.items():
        starts = pd.date_range(start, end, freq=f"{window_years - overlap_years}YS")
        chained = None
        for s in starts:
            e = min(s + pd.DateOffset(years=window_years), pd.Timestamp(end))
            w = _trends_window(pytrends, term, s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d"))
            if chained is None:
                chained = w
            else:
                common = chained.index.intersection(w.index)
                ratio = (chained.loc[common] / w.loc[common].replace(0, np.nan)).median()
                chained = pd.concat([chained, w.loc[w.index > chained.index.max()] * ratio])
            time.sleep(5)  # Trends rate-limits aggressively
            if e >= pd.Timestamp(end):
                break
        frames.append(pd.DataFrame({"date": chained.index, "series": f"trends:{label}", "value": chained.values}))
        print(f"  Trends {label}: {len(chained)} weeks", file=sys.stderr)
    return pd.concat(frames)


# ---------- GDELT news volume (DOC 2.0 API, free) ----------
def _parse_doc_timeline(js: dict) -> pd.DataFrame:
    """TimelineVolRaw JSON -> date, matching articles, all monitored articles."""
    rows = js["timeline"][0]["data"]
    return pd.DataFrame({
        "date": pd.to_datetime([r["date"][:8] for r in rows], format="%Y%m%d"),
        "count": [r["value"] for r in rows],
        "total": [r.get("norm", np.nan) for r in rows],
    })


def gdelt_doc(queries=GDELT_DOC_QUERIES, start=START, end=END, chunk_months=6) -> pd.DataFrame:
    """Daily share of English-language articles (per million monitored) matching each query.
    Normalising by all monitored articles removes drift in GDELT's coverage. Coverage starts 2017."""
    frames = []
    for label, q in queries.items():
        parts = []
        for a in pd.date_range(start, end, freq=f"{chunk_months}MS"):
            b = min(a + pd.DateOffset(months=chunk_months), pd.Timestamp(end))
            params = {"query": f"{q} sourcelang:english", "mode": "timelinevolraw", "format": "json",
                      "timelinesmooth": 0, "startdatetime": a.strftime("%Y%m%d000000"),
                      "enddatetime": b.strftime("%Y%m%d000000")}
            url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            for k in range(4):
                try:
                    parts.append(_parse_doc_timeline(json.load(urllib.request.urlopen(req, timeout=120))))
                    break
                except Exception as e:  # rate limit (one request per ~5 s) or a transient error
                    print(f"  GDELT {label} {a.date()}: {type(e).__name__}; retrying", file=sys.stderr)
                    time.sleep(30 * (k + 1))
            else:
                raise RuntimeError(f"GDELT DOC API kept failing for {label} {a.date()}")
            time.sleep(6)
        d = pd.concat(parts).drop_duplicates("date").sort_values("date")
        d = d[d["date"] < pd.Timestamp(end)]
        if d["total"].isna().all():
            raise RuntimeError("GDELT response had no 'norm' totals; cannot normalise")
        frames.append(pd.DataFrame({"date": d["date"], "series": f"gdelt:{label}",
                                    "value": d["count"] / d["total"] * 1e6}))
        print(f"  GDELT {label}: {len(d)} days", file=sys.stderr)
    return pd.concat(frames)


# ---------- GDELT news volume (BigQuery) ----------
def gdelt_sql(terms=GDELT_TERMS, start=START, end=END) -> str:
    """Daily count of GKG documents whose all-names/themes field mentions any term."""
    cond = " OR ".join(f"LOWER(AllNames) LIKE '%{t.lower()}%'" for t in terms)
    return f"""-- Runs against the public GDELT 2.0 GKG table; check bytes scanned before running.
SELECT DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', CAST(DATE AS STRING))) AS date,
       'gdelt:ai_mentions' AS series,
       COUNT(*) AS value
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE _PARTITIONTIME BETWEEN TIMESTAMP('{start}') AND TIMESTAMP('{end}')
  AND ({cond})
GROUP BY date, series
ORDER BY date
"""


# ---------- Index construction ----------
def build_index(long: pd.DataFrame, freq: str = "W-MON") -> pd.DataFrame:
    """Weekly attention index.

    Each series: weekly mean -> log1p -> z-score over the full sample.
    index_mean = equal-weight mean of z-scores; index_pc1 = first principal component
    (sign fixed to correlate positively with index_mean), rescaled to unit variance.
    """
    long = long.copy()
    long["date"] = pd.to_datetime(long["date"])
    wide = (long.pivot_table(index="date", columns="series", values="value", aggfunc="sum")
                .resample(freq).mean())
    z = np.log1p(wide)
    z = (z - z.mean()) / z.std(ddof=0)
    out = pd.DataFrame(index=z.index)
    out["index_mean"] = z.mean(axis=1, skipna=True)
    complete = z.dropna()
    if complete.shape[1] >= 2 and len(complete) > 10:
        u, s, vt = np.linalg.svd(complete.values - complete.values.mean(0), full_matrices=False)
        pc1 = pd.Series(u[:, 0] * s[0], index=complete.index)
        if np.corrcoef(pc1, out.loc[complete.index, "index_mean"])[0, 1] < 0:
            pc1 = -pc1
        out["index_pc1"] = (pc1 - pc1.mean()) / pc1.std(ddof=0)
        out["pc1_share"] = float(s[0] ** 2 / (s ** 2).sum())
    return out.join(z.add_prefix("z:")).rename_axis("week").reset_index()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["wikipedia", "trends", "gdelt-doc", "gdelt-sql", "index"])
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--inputs", nargs="*", type=pathlib.Path, default=[])
    args = ap.parse_args()
    if args.cmd == "gdelt-sql":
        sys.stdout.write(gdelt_sql())
        return
    if args.cmd == "wikipedia":
        df = wikipedia()
    elif args.cmd == "trends":
        df = trends()
    elif args.cmd == "gdelt-doc":
        df = gdelt_doc()
    else:
        df = build_index(pd.concat(pd.read_csv(p) for p in args.inputs))
    df.to_csv(args.out, index=False)
    print(f"wrote {args.out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
