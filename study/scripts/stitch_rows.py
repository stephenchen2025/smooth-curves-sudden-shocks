"""Stitch overlapping HF windows into one daily series per article; report overlap agreement."""
import json, pathlib, sys
import pandas as pd
rows_dir, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
series = {}
for p in sorted(rows_dir.glob("*.json")):
    r = json.loads(p.read_text())
    vals = r["history"] + r["target"]
    assert len(r["history"]) == 365 and len(r["target"]) == 28, (p.name, len(r["history"]), len(r["target"]))
    days = pd.date_range(r["history_start"], periods=len(vals), freq="D")
    assert days[-1] == pd.Timestamp(r["target_end"]), p.name
    s = pd.Series(vals, index=days, dtype=float)
    art = r["article"]
    if art in series:
        prev = series[art]
        common = prev.index.intersection(s.index)
        mism = (prev.loc[common] != s.loc[common]).sum()
        print(f"{p.name}: overlap {len(common)} days, mismatches {mism}")
        series[art] = prev.combine_first(s)
    else:
        series[art] = s
long = []
for art, s in series.items():
    full = pd.date_range(s.index.min(), s.index.max(), freq="D")
    gaps = len(full.difference(s.index))
    print(f"{art}: {s.index.min().date()}..{s.index.max().date()}, {len(s)} days, gaps {gaps}")
    long.append(pd.DataFrame({"date": s.index, "series": f"wiki:{art}", "value": s.values.astype(int)}))
pd.concat(long).to_csv(out, index=False)
