"""EXPLORATORY (not pre-registered): A2 after removing week-of-year means; A2 on the 3-article mean index."""
import pathlib, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import analyze as an
root = pathlib.Path(__file__).resolve().parents[1]
V = pd.read_csv(root/"out/attention/attention_index.csv", index_col=0, parse_dates=True)
ev = pd.read_csv(root/"data/events.csv"); hz=[root/"out/horizons_1-0.csv", root/"out/horizons_1-1.csv"]
def frame(A):
    df = pd.DataFrame({"A": A}); df["V"]=an.weekly_events(ev, A.index, "visibility"); df["P"]=an.weekly_events(ev, A.index, "policy")
    return df.join(an.capability_surprise(hz, A.index))
def cum(d, t): r=an.lp_attention(d); return r[(r.term==t)&r.h.between(0,4)].coef.sum()
def perm(df, col, t, n=300, seed=0):
    rng=np.random.default_rng(seed); obs=cum(df,t); null=[]
    for _ in range(n):
        d=df.copy(); d[col]=np.roll(d[col].values, rng.integers(26,len(d)-26)); null.append(cum(d,t))
    return round(float(obs),3), round(float(np.mean(np.abs(null)>=abs(obs))),3)
woy = V.index.isocalendar().week.values
out = {}
for name, A in [("pc1_deseasonalized", V.pc1 - V.pc1.groupby(woy).transform("mean")), ("mean_all", V.mean_all)]:
    df = frame(A)
    r = an.lp_attention(df)
    out[name] = {"V_h0": round(float(r.query("h==0 and term=='V'").coef.iloc[0]),3),
                 "V_h0_se": round(float(r.query("h==0 and term=='V'").se.iloc[0]),3),
                 "cum_V": perm(df,"V","V"), "cum_M": perm(df,"M","M")}
print(json.dumps(out, indent=1)); json.dump(out, open(root/"out/attention/exploratory.json","w"), indent=1)
