"""Capability series from METR's public run-level data.

Replicates METR's headline time-horizon fit for each model:
logistic regression of binarized success on log2(human minutes),
task weights = invsqrt_task_weight (renormalised per model),
L2 regularisation 1e-5 (sklearn C = 1e5).

Usage:
    python capability.py --repo /path/to/eval-analysis-public --version 1-0 --out horizons_1-0.csv
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression

REGULARIZATION = 1e-5
WEIGHT_COL = "invsqrt_task_weight"


def load_runs(repo: pathlib.Path, version: str) -> pd.DataFrame:
    path = repo / "reports" / f"time-horizon-{version}" / "data" / "raw" / "runs.jsonl"
    rows = [json.loads(line) for line in path.open()]
    runs = pd.DataFrame(rows)
    return runs[runs["alias"] != "human"].copy()


def load_release_dates(repo: pathlib.Path) -> dict[str, str]:
    dates = yaml.safe_load((repo / "data" / "external" / "release_dates.yaml").read_text())["date"]
    return {k: str(v) for k, v in dates.items()}


def fit_horizon(minutes: np.ndarray, success: np.ndarray, weights: np.ndarray,
                quantiles=(0.5, 0.8)) -> dict[str, float]:
    """Weighted logistic fit; returns horizons in minutes at each success quantile."""
    weights = weights / weights.sum()
    x = np.log2(minutes).reshape(-1, 1)
    y = success.astype(float)
    if y.max() == 0:
        return {f"p{int(q * 100)}": 0.0 for q in quantiles} | {"slope": float("nan")}
    # split fractional scores into weighted 0/1 rows, as METR does
    frac = (y > 0) & (y < 1)
    if frac.any():
        x = np.vstack([x[~frac], x[frac], x[frac]])
        w = np.concatenate([weights[~frac], (1 - y[frac]) * weights[frac], y[frac] * weights[frac]])
        y = np.concatenate([y[~frac], np.zeros(frac.sum()), np.ones(frac.sum())])
        weights = w
    model = LogisticRegression(C=1 / REGULARIZATION, max_iter=1000)
    model.fit(x, y, sample_weight=weights)
    a, b = model.intercept_[0], model.coef_[0][0]
    out = {"slope": b}
    for q in quantiles:
        out[f"p{int(q * 100)}"] = float(np.exp2((np.log(q / (1 - q)) - a) / b))
    return out


def horizons(runs: pd.DataFrame, release_dates: dict[str, str], n_boot: int = 0,
             seed: int = 0) -> pd.DataFrame:
    """Point estimates per model, plus optional task-family bootstrap draws of log2(p50)."""
    rng = np.random.default_rng(seed)
    records = []
    for alias, g in runs.groupby("alias"):
        est = fit_horizon(g["human_minutes"].values, g["score_binarized"].values, g[WEIGHT_COL].values)
        rec = {"model": alias, "release_date": release_dates.get(alias), **est, "n_runs": len(g)}
        if n_boot:
            fams = g["task_family"].unique()
            draws = []
            for _ in range(n_boot):
                pick = rng.choice(fams, size=len(fams), replace=True)
                gb = pd.concat([g[g["task_family"] == f] for f in pick])
                draws.append(np.log2(max(fit_horizon(gb["human_minutes"].values,
                                                      gb["score_binarized"].values,
                                                      gb[WEIGHT_COL].values)["p50"], 1e-6)))
            rec["log2_p50_boot_sd"] = float(np.std(draws, ddof=1))
        records.append(rec)
    df = pd.DataFrame(records)
    missing = df[df["release_date"].isna()]["model"].tolist()
    if missing:
        print("No release date for:", missing)
    df = df.dropna(subset=["release_date"])
    df["release_date"] = pd.to_datetime(df["release_date"])
    return df.sort_values("release_date").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=pathlib.Path, required=True)
    ap.add_argument("--version", choices=["1-0", "1-1"], required=True)
    ap.add_argument("--n-boot", type=int, default=0)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()
    runs = load_runs(args.repo, args.version)
    df = horizons(runs, load_release_dates(args.repo), n_boot=args.n_boot)
    df.to_csv(args.out, index=False)
    print(df[["model", "release_date", "p50", "p80"]].to_string(index=False))


if __name__ == "__main__":
    main()
