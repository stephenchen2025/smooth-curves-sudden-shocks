"""H2-H4: attention, capability surprise and policy timing (weekly local projections).

    python analyze.py --attention data/attention_index.csv --events data/events.csv \
        --horizons out/horizons_1-0.csv out/horizons_1-1.csv --out out/
    python analyze.py --simulate        # checks the estimators recover planted effects

A2 (H2)  Attention response to visibility events vs capability milestones:
         A[t+h] - A[t-1] = a_h + b_h*V[t] + g_h*M[t] + lags(dA) + e      h = -4..12
A3 (H3)  Policy events on attention and capability surprise (Poisson local projections):
         E[P[t+h]] = exp(a_h + th_h*dA[t] + ph_h*S[t] + lags(P) + trend)  h = 0..12
A4 (H4)  Decay: policy-event rate by weeks since an attention spike (Poisson, half-life).
Inference: Newey-West (HAC) errors plus a permutation test that shuffles event weeks.
"""
from __future__ import annotations

import argparse
import pathlib

import numpy as np
import pandas as pd
import statsmodels.api as sm

FREQ = "W-MON"  # weeks end on Monday; weekly rows are labelled by that Monday
H_A2 = range(-4, 13)
H_A3 = range(0, 13)


# ---------- inputs ----------
def weekly_events(events: pd.DataFrame, index: pd.DatetimeIndex, cls: str, scope: str | None = None) -> pd.Series:
    e = events[events["event_class"] == cls]
    if scope:
        e = e[e["scope"] == scope]
    wk = pd.to_datetime(e["date"]).dt.to_period(FREQ).dt.end_time.dt.normalize()
    return wk.value_counts().reindex(index, fill_value=0).astype(float)


def capability_surprise(horizon_files: list[pathlib.Path], index: pd.DatetimeIndex) -> pd.DataFrame:
    """Frontier-setting releases and their real-time surprise: log2(p50) minus the
    trend fitted on all earlier frontier releases in the same METR version."""
    recs = []
    cutoff = None
    for f in sorted(horizon_files):  # 1-0 before 1-1
        df = pd.read_csv(f, parse_dates=["release_date"]).query("p50 > 0").sort_values("release_date")
        df["y"] = np.log2(df["p50"])
        df["t"] = (df["release_date"] - pd.Timestamp("2019-01-01")).dt.days / 365.25
        df = df[df["y"] > df["y"].cummax().shift(fill_value=-np.inf)]
        for i in range(3, len(df)):
            prev, row = df.iloc[:i], df.iloc[i]
            if cutoff is not None and row["release_date"] <= cutoff:
                continue
            fit = sm.OLS(prev["y"], sm.add_constant(prev["t"])).fit()
            pred = fit.params["const"] + fit.params["t"] * row["t"]
            recs.append({"date": row["release_date"], "model": row["model"], "surprise": row["y"] - pred})
        cutoff = df["release_date"].max()
    s = pd.DataFrame(recs)
    wk = s["date"].dt.to_period(FREQ).dt.end_time.dt.normalize()
    out = pd.DataFrame(index=index)
    out["M"] = wk.value_counts().reindex(index, fill_value=0).astype(float)
    out["S"] = s.groupby(wk)["surprise"].sum().reindex(index, fill_value=0.0)
    return out


# ---------- estimators ----------
def lp_attention(df: pd.DataFrame, lags: int = 2) -> pd.DataFrame:
    """A2: local projections of attention on visibility (V) and milestone (M) weeks."""
    rows = []
    dA = df["A"].diff()
    for h in H_A2:
        y = df["A"].shift(-h) - df["A"].shift(1)
        X = pd.DataFrame({"V": df["V"], "M": df["M"]})
        for k in range(1, lags + 1):
            X[f"dA_l{k}"] = dA.shift(k)
        d = pd.concat([y.rename("y"), X], axis=1).dropna()
        fit = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit(
            cov_type="HAC", cov_kwds={"maxlags": max(abs(h), 1) + 1})
        for var in ("V", "M"):
            rows.append({"h": h, "term": var, "coef": fit.params[var], "se": fit.bse[var]})
    return pd.DataFrame(rows)


def lp_policy(df: pd.DataFrame, lags: int = 2) -> pd.DataFrame:
    """A3: Poisson local projections of weekly policy events on dA and capability surprise."""
    rows = []
    dA = df["A"].diff()
    trend = np.arange(len(df)) / 52.0
    for h in H_A3:
        y = df["P"].shift(-h)
        X = pd.DataFrame({"dA": dA, "S": df["S"], "trend": trend}, index=df.index)
        for k in range(1, lags + 1):
            X[f"P_l{k}"] = df["P"].shift(k)
        d = pd.concat([y.rename("y"), X], axis=1).dropna()
        fit = sm.GLM(d["y"], sm.add_constant(d.drop(columns="y")), family=sm.families.Poisson()).fit(
            cov_type="HAC", cov_kwds={"maxlags": h + 1})
        for var in ("dA", "S"):
            rows.append({"h": h, "term": var, "coef": fit.params[var], "se": fit.bse[var]})
    return pd.DataFrame(rows)


def spike_weeks(A: pd.Series, k: float = 2.0, gap: int = 8) -> list[pd.Timestamp]:
    dA = A.diff()
    cand = dA[dA > k * dA.std()].index
    keep: list[pd.Timestamp] = []
    for w in cand:  # keep the first week of each spike, at least `gap` weeks apart
        if not keep or (w - keep[-1]).days >= gap * 7:
            keep.append(w)
    return keep


def decay(df: pd.DataFrame, horizon: int = 26) -> dict:
    """A4: how fast does excess policy activity fade after an attention spike?

    Pooled over spikes, weeks k = 0..horizon after each spike:
        log E[P_k] = log(baseline) + a + c * r**k
    where baseline is the spike's mean weekly rate over the previous 26 weeks.
    r is chosen by profile likelihood on a grid; half-life = ln 2 / -ln r weeks.
    """
    rows = []
    for j, w in enumerate(spike_weeks(df["A"])):
        i = df.index.get_loc(w)
        base = df["P"].iloc[max(0, i - 26):i].mean()
        for k in range(0, horizon + 1):
            if i + k < len(df):
                rows.append({"spike": j, "k": k, "P": df["P"].iloc[i + k], "base": base})
    d = pd.DataFrame(rows)
    if d.empty or d["P"].sum() == 0:
        return {"n_spikes": 0}
    offset = np.log(d["base"].clip(lower=0.05))
    best = None
    for r in np.linspace(0.30, 0.99, 70):
        X = sm.add_constant(pd.DataFrame({"excess": r ** d["k"]}))
        fit = sm.GLM(d["P"], X, family=sm.families.Poisson(), offset=offset).fit()
        if best is None or fit.llf > best[1]:
            best = (r, fit.llf, fit.params["excess"])
    r, _, c = best
    return {"n_spikes": int(d["spike"].nunique()), "decay_rate_r": round(float(r), 3),
            "initial_excess_log": round(float(c), 3),
            "half_life_weeks": round(float(np.log(2) / -np.log(r)), 2)}


def permutation_p(df: pd.DataFrame, col: str, stat_fn, n: int = 500, seed: int = 0) -> float:
    """Shuffle the weeks in which `col` events occur (circular shift keeps their spacing)."""
    rng = np.random.default_rng(seed)
    obs = stat_fn(df)
    null = []
    for _ in range(n):
        d = df.copy()
        d[col] = np.roll(d[col].values, rng.integers(26, len(d) - 26))
        null.append(stat_fn(d))
    return float(np.mean(np.abs(null) >= abs(obs)))


def cum_effect(term: str, hmax: int = 4):
    def f(d: pd.DataFrame) -> float:
        r = lp_attention(d)
        return r[(r["term"] == term) & (r["h"].between(0, hmax))]["coef"].sum()
    return f


# ---------- simulation self-test ----------
def simulate(weeks: int = 400, beta_v: float = 1.5, beta_m: float = 0.0, theta: float = 0.6,
             phi: float = 0.0, policy_memory: float = 0.85, seed: int = 1) -> pd.DataFrame:
    """Planted world: visibility events raise attention (decaying), milestones do not;
    policy intensity jumps with attention increases, decays at rate `policy_memory`
    (half-life ln2 / -ln(policy_memory) weeks) and ignores capability surprise."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2019-01-07", periods=weeks, freq=FREQ)
    V = (rng.random(weeks) < 0.03).astype(float)
    M = (rng.random(weeks) < 0.06).astype(float)
    S = M * rng.normal(0, 0.7, weeks)
    A = np.zeros(weeks)
    for t in range(1, weeks):
        A[t] = 0.85 * A[t - 1] + beta_v * V[t] + beta_m * M[t] + rng.normal(0, 0.3)
    dA = np.diff(A, prepend=0)
    X = np.zeros(weeks)  # excess policy intensity carried forward from attention jumps
    for t in range(1, weeks):
        X[t] = policy_memory * X[t - 1] + theta * max(dA[t], 0.0)
    lam = np.exp(-1.0 + X + phi * S)
    P = rng.poisson(lam).astype(float)
    return pd.DataFrame({"A": A, "V": V, "M": M, "S": S, "P": P}, index=idx)


def self_test() -> None:
    df = simulate()
    a2 = lp_attention(df)
    a3 = lp_policy(df)
    print("A2 impact (h=0): V planted 1.5 ->", round(a2.query("h==0 and term=='V'")["coef"].item(), 2),
          "| M planted 0.0 ->", round(a2.query("h==0 and term=='M'")["coef"].item(), 2))
    print("A3 (h=0): dA planted 0.6 ->", round(a3.query("h==0 and term=='dA'")["coef"].item(), 2),
          "| S planted 0.0 ->", round(a3.query("h==0 and term=='S'")["coef"].item(), 2))
    pre = a2.query("h<0 and term=='V'")["coef"].abs().max()
    print("A2 pre-trend check, max |V coef| for h<0:", round(pre, 2))
    print("Permutation p for V cumulative effect:", permutation_p(df, "V", cum_effect("V"), n=200))
    print("Permutation p for M cumulative effect:", permutation_p(df, "M", cum_effect("M"), n=200))
    print("A4:", decay(df), "| planted half-life:", round(np.log(2) / -np.log(0.85), 2), "weeks")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--attention", type=pathlib.Path)
    ap.add_argument("--attention-col", default="index_pc1")
    ap.add_argument("--events", type=pathlib.Path)
    ap.add_argument("--horizons", nargs="*", type=pathlib.Path, default=[])
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("out"))
    args = ap.parse_args()
    if args.simulate:
        self_test()
        return
    att = pd.read_csv(args.attention, parse_dates=["week"]).set_index("week")
    idx = att.index
    events = pd.read_csv(args.events)
    df = pd.DataFrame(index=idx)
    df["A"] = att[args.attention_col]
    df["V"] = weekly_events(events, idx, "visibility")
    df["P"] = weekly_events(events, idx, "policy")
    df = df.join(capability_surprise(args.horizons, idx))
    args.out.mkdir(parents=True, exist_ok=True)
    lp_attention(df).to_csv(args.out / "a2_attention_lp.csv", index=False)
    lp_policy(df).to_csv(args.out / "a3_policy_lp.csv", index=False)
    pd.Series(decay(df)).to_csv(args.out / "a4_decay.csv")
    pd.Series({"V": permutation_p(df, "V", cum_effect("V")),
               "M": permutation_p(df, "M", cum_effect("M"))}).to_csv(args.out / "a2_permutation_p.csv")
    print("wrote results to", args.out)


if __name__ == "__main__":
    main()
