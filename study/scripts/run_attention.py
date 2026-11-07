"""Run A2-A4 on a weekly attention index, plus the pre-registered robustness grid.

    python scripts/run_attention.py                                  # first run: Wikipedia via the HF copy
    python scripts/run_attention.py --inputs data/wiki.csv data/trends.csv data/gdelt.csv --out out/attention_full

Index rules (data/FREEZE.md): each series is averaged to W-MON weeks; a series enters from the first week
its weekly value reaches a quarter of its median (so pre-launch zeros and pre-creation redirect traffic
are not read as attention); log1p; z-score. The main index is the first principal component of the series
present in every week of the sample; series that start later enter only the equal-weight index.
"""
import argparse, json, pathlib, sys
import numpy as np, pandas as pd
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import analyze as an

ap = argparse.ArgumentParser()
ap.add_argument("--inputs", nargs="+", type=pathlib.Path, default=[root / "data/wiki_hf.csv"])
ap.add_argument("--out", type=pathlib.Path, default=root / "out/attention")
ap.add_argument("--start", default="2021-01-05")  # first Tuesday: full W-MON weeks; events are coded from 2021
ap.add_argument("--end", default="2026-09-28")    # last Monday before the event coding stops
ap.add_argument("--n-perm", type=int, default=500)
args = ap.parse_args()
out = args.out; out.mkdir(parents=True, exist_ok=True)

daily = pd.concat(pd.read_csv(p, parse_dates=["date"]) for p in args.inputs)
daily = daily[(daily.date >= args.start) & (daily.date <= args.end)]


def weekly(agg):
    wk = daily.pivot_table(index="date", columns="series", values="value", aggfunc="sum").resample("W-MON").agg(agg)
    for c in wk:  # late start: before the first week at >= 25% of the series' median
        ok = wk[c] >= 0.25 * wk[c].median()
        if ok.any():
            wk.loc[wk.index < ok.idxmax(), c] = np.nan
    return wk


def pc1(z):
    u, s, _ = np.linalg.svd(z.values - z.values.mean(0), full_matrices=False)
    p = pd.Series(u[:, 0] * s[0], index=z.index)
    if np.corrcoef(p, z.mean(axis=1))[0, 1] < 0:
        p = -p
    return (p - p.mean()) / p.std(ddof=0), float(s[0] ** 2 / (s ** 2).sum())


def index_variants(agg="mean"):
    z = np.log1p(weekly(agg)); z = (z - z.mean()) / z.std(ddof=0)
    complete = [c for c in z if z[c].notna().all()]
    v = pd.DataFrame(index=z.index)
    if len(complete) >= 2:
        v["pc1"], share = pc1(z[complete])
    else:
        v["pc1"], share = z[complete[0]], 1.0
    v["mean_all"] = z.mean(axis=1, skipna=True)
    for c in z:
        v[f"z:{c}"] = z[c]
    v.attrs.update(pc1_share=share, complete=complete, late=[c for c in z if c not in complete])
    return v


events = pd.read_csv(root / "data/events.csv")
hz = [root / "out/horizons_1-0.csv", root / "out/horizons_1-1.csv"]


def frame(A, frontier_only=False):
    A = A.dropna(); idx = A.index
    df = pd.DataFrame({"A": A})
    df["V"] = an.weekly_events(events, idx, "visibility")
    df["P"] = an.weekly_events(events, idx, "policy", "frontier" if frontier_only else None)
    return df.join(an.capability_surprise(hz, idx))


def cum(r, term, hmax=4):
    return r[(r.term == term) & r.h.between(0, hmax)]["coef"].sum()


def perm(df, col, fn, n=args.n_perm, seed=0):
    rng = np.random.default_rng(seed); obs = fn(df); null = []
    for _ in range(n):
        d = df.copy(); d[col] = np.roll(d[col].values, rng.integers(26, len(d) - 26)); null.append(fn(d))
    return float(obs), float(np.mean(np.abs(np.array(null)) >= abs(obs)))


V = index_variants("mean"); Vmed = index_variants("median")
V.to_csv(out / "attention_index.csv", index_label="week")
res = {"inputs": [str(p) for p in args.inputs], "series_in_pc1": V.attrs["complete"],
       "late_starters": V.attrs["late"], "pc1_share": V.attrs["pc1_share"], "weeks": len(V),
       "first_week": str(V.index.min().date()), "last_week": str(V.index.max().date())}

# ---- main specification ----
df = frame(V["pc1"])
res["counts"] = {k: int(df[k].sum()) for k in ("V", "P", "M")}
a2 = an.lp_attention(df); a3 = an.lp_policy(df)
a2.to_csv(out / "a2_attention_lp.csv", index=False); a3.to_csv(out / "a3_policy_lp.csv", index=False)
res["a2_cum_V"] = perm(df, "V", lambda d: cum(an.lp_attention(d), "V"))
res["a2_cum_M"] = perm(df, "M", lambda d: cum(an.lp_attention(d), "M"))
res["a2_pretrend_maxabs_V"] = float(a2.query("h<0 and term=='V'")["coef"].abs().max())
res["a2_pretrend_maxabs_M"] = float(a2.query("h<0 and term=='M'")["coef"].abs().max())
res["a3_cum_dA"] = perm(df, "P", lambda d: cum(an.lp_policy(d), "dA"))
res["a3_cum_S"] = perm(df, "S", lambda d: cum(an.lp_policy(d), "S"))
res["a4"] = an.decay(df)
spikes = an.spike_weeks(df["A"]); res["spikes"] = [str(s.date()) for s in spikes]
# A4 null: does policy activity rise after random weeks as much as after spikes?
rng = np.random.default_rng(1); null = []
for _ in range(300):
    d = df.copy(); d["A"] = np.roll(d["A"].values, rng.integers(26, len(d) - 26))
    null.append(an.decay(d).get("initial_excess_log", 0.0))
res["a4_c_perm_p"] = float(np.mean(np.array(null) >= res["a4"].get("initial_excess_log", 0)))
# A4 interval: bootstrap over spikes
orig = an.spike_weeks; hl = []
for b in range(300):
    pick = sorted(rng.choice(len(spikes), len(spikes), replace=True))
    an.spike_weeks = lambda A, k=2.0, gap=8, _p=pick: [spikes[i] for i in _p]
    hl.append(an.decay(df).get("half_life_weeks", np.nan))
an.spike_weeks = orig
res["a4_half_life_boot_iqr"] = [float(np.nanpercentile(hl, 25)), float(np.nanpercentile(hl, 75))]

# Pew validity check: Dec 2022 vs Aug 2023
res["validity_dec22_vs_aug23"] = [float(V.loc["2022-12", "pc1"].mean()), float(V.loc["2023-08", "pc1"].mean())]

# Where the headline shocks rank among weekly rises (1 = largest)
dA = V["pc1"].diff()
res["shock_rank"] = {lab: int((dA > dA.loc[pd.Timestamp(w)]).sum()) + 1 for lab, w in
                     [("ChatGPT", "2022-12-05"), ("GPT-4", "2023-03-20"), ("DeepSeek-R1", "2025-01-27"),
                      ("HF intrusion", "2026-07-20")]}

# ---- robustness grid ----
grid = []
variants = [("pc1", V.pc1), ("mean_all", V.mean_all)] + [(c, V[c]) for c in V if c.startswith("z:")] \
    + [("pc1_weekly_median", Vmed.pc1)]
for name, A in variants:
    for fo in (False, True):
        d = frame(A, fo)
        for lags in (1, 2, 3, 4):
            r2 = an.lp_attention(d, lags=lags); r3 = an.lp_policy(d, lags=lags)
            grid.append({"index": name, "frontier_only_P": fo, "lags": lags,
                         "a2_cum_V": cum(r2, "V"), "a2_cum_M": cum(r2, "M"),
                         "a3_cum_dA": cum(r3, "dA"), "a3_cum_S": cum(r3, "S")})
        for k in (1.5, 2.0, 2.5):
            an.spike_weeks = lambda A_, k_=k, gap=8: orig(A_, k=k_, gap=gap)
            r4 = an.decay(d); an.spike_weeks = orig
            grid.append({"index": name, "frontier_only_P": fo, "spike_k": k, **{f"a4_{x}": y for x, y in r4.items()}})
pd.DataFrame(grid).to_csv(out / "robustness_grid.csv", index=False)
json.dump(res, open(out / "summary.json", "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
