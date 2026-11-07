"""Check the Hugging Face copy of the pageviews against a fresh pull from the Wikimedia API.

    python scripts/compare_wiki.py data/wiki.csv data/wiki_hf.csv
"""
import sys
import pandas as pd

api, hf = (pd.read_csv(p, parse_dates=["date"]) for p in sys.argv[1:3])
m = api.merge(hf, on=["date", "series"], suffixes=("_api", "_hf"))
if m.empty:
    sys.exit("no overlapping series and dates")
for s, g in m.groupby("series"):
    rel = (g.value_api - g.value_hf).abs() / g.value_hf.clip(lower=1)
    print(f"{s}: {len(g)} days, exact {(g.value_api == g.value_hf).mean():.1%}, "
          f"median abs diff {rel.median():.2%}, max {rel.max():.2%}")
