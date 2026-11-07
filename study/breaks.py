"""H1: does the capability trend break at the perception-shock dates?

Three tests per shock date s, on log2(p50 horizon) against release date:
  1. Out-of-sample prediction: fit the trend on models released before s and
     ask whether models released in [s, s + window) sit above or below it.
  2. Chow-style break: full-sample OLS with a level shift and slope change at s;
     joint Wald test (HC3 robust) that both are zero.
  3. Placebo scan: the same break test at every month-start in the data; where does
     the shock date's statistic rank among arbitrary dates?

Usage:
    python breaks.py --horizons out/horizons_1-0.csv --label "TH 1.0" --out out/breaks_1-0.csv
"""
from __future__ import annotations

import argparse
import pathlib

import numpy as np
import pandas as pd
import statsmodels.api as sm

SHOCKS = {
    "ChatGPT launch": "2022-11-30",
    "DeepSeek-R1 release": "2025-01-20",
    "Hugging Face intrusion attributed": "2026-07-21",
}
ORIGIN = pd.Timestamp("2019-01-01")


def prep(df: pd.DataFrame, frontier: bool) -> pd.DataFrame:
    df = df[df["p50"] > 0].copy()
    df["t"] = (df["release_date"] - ORIGIN).dt.days / 365.25
    df["y"] = np.log2(df["p50"])
    df = df.sort_values(["release_date", "y"], ascending=[True, False])
    if frontier:  # state of the art at release: beats every earlier model
        df = df[df["y"] > df["y"].cummax().shift(fill_value=-np.inf)]
    return df.reset_index(drop=True)


def prediction_test(df: pd.DataFrame, s: pd.Timestamp, window_days: int = 548) -> dict:
    pre = df[df["release_date"] < s]
    post = df[(df["release_date"] >= s) & (df["release_date"] < s + pd.Timedelta(days=window_days))]
    if len(pre) < 3 or len(post) < 1:
        return {"n_pre": len(pre), "n_post": len(post)}
    X = sm.add_constant(pre["t"])
    fit = sm.OLS(pre["y"], X).fit()
    Xp = sm.add_constant(post["t"], has_constant="add")
    pred = fit.get_prediction(Xp)
    resid = post["y"].values - pred.predicted_mean
    # covariance of prediction errors: parameter uncertainty + residual variance
    cov = Xp.values @ fit.cov_params().values @ Xp.values.T + fit.scale * np.eye(len(post))
    stat = float(resid @ np.linalg.solve(cov, resid))
    from scipy import stats
    p_joint = float(1 - stats.f.cdf(stat / len(post), len(post), fit.df_resid))
    return {
        "n_pre": len(pre), "n_post": len(post),
        "pre_doubling_months": 12 / fit.params["t"],
        "mean_error_doublings": float(resid.mean()),
        "p_joint": p_joint,
    }


MIN_SIDE = 5  # models needed on each side of a candidate break


def break_stat(df: pd.DataFrame, s: pd.Timestamp) -> tuple[float, float] | None:
    """Chow-style F test for a level shift plus slope change at s (classical OLS errors;
    robust errors are unstable with this few models per side)."""
    ts = (s - ORIGIN).days / 365.25
    post = (df["t"] >= ts).astype(float)
    if post.sum() < MIN_SIDE or (1 - post).sum() < MIN_SIDE:
        return None
    X = pd.DataFrame({"const": 1.0, "t": df["t"], "level": post, "slope": post * (df["t"] - ts)})
    fit = sm.OLS(df["y"], X).fit()
    f = fit.f_test("level = 0, slope = 0")
    return float(np.squeeze(f.fvalue)), float(f.pvalue)


def placebo_rank(df: pd.DataFrame, s: pd.Timestamp) -> tuple[float, int]:
    months = pd.date_range(df["release_date"].min(), df["release_date"].max(), freq="MS")
    stats_ = [r[0] for m in months if (r := break_stat(df, m)) is not None]
    own = break_stat(df, s)
    if own is None or not stats_:
        return float("nan"), len(stats_)
    return float(np.mean(np.array(stats_) >= own[0])), len(stats_)


def run(df_raw: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for frontier in (True, False):
        df = prep(df_raw, frontier)
        whole = sm.OLS(df["y"], sm.add_constant(df["t"])).fit()
        for name, date in SHOCKS.items():
            s = pd.Timestamp(date)
            rec = {"data": label, "sample": "frontier" if frontier else "all models", "shock": name,
                   "trend_doubling_months_full": 12 / whole.params["t"], "n_models": len(df)}
            if s > df["release_date"].max():
                rec["note"] = "after last model in data"
                rows.append(rec)
                continue
            rec.update(prediction_test(df, s))
            bs = break_stat(df, s)
            if bs:
                rec["break_wald"], rec["break_p"] = bs
                rec["placebo_share_as_large"], rec["placebo_n"] = placebo_rank(df, s)
            rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizons", type=pathlib.Path, required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.horizons, parse_dates=["release_date"])
    res = run(df, args.label)
    res.to_csv(args.out, index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(res.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
