# Frozen before the AI attention series was examined

Frozen at: 2026-11-07T05:21:18Z
data/events.csv sha256: 2fa44eeb71e03cd5428b03c30032910ba1d38198d0251c6f279fc1b5ed30225a  (43 policy, 20 visibility events, 2021-04-21 to 2026-09-03)
analyze.py sha256: f4a4b19c856a10411d6e082e9dfb3dbd5a7ddf20f73172752757b1d28b9c232b

## Attention data (decided before viewing the AI series)
- Source: Wikipedia daily user pageviews (en, all-access), via the CC0 Hugging Face dataset
  itsalissonsilva/wikimedia-pageviews-forecasting (built from the Wikimedia REST API, retrieved 2026-10-31).
  The direct API, Google Trends and GDELT are unreachable from this workspace.
- Series: Artificial_intelligence, Machine_learning, Large_language_model (the AI articles in that cohort;
  Transformer and Gemma excluded as technical/late-starting).
- Sample: weeks covered by daily data from 2021-01-01 to 2026-10-02 (last complete window in the dataset).
- Index: weekly mean -> log1p -> z-score; main index = first principal component of the series with complete
  coverage over the sample; a series that starts later enters only the equal-weight robustness index.
- Robustness: equal-weight index; each series alone; spike threshold 1.5/2/2.5 SD; LP lags 1-4; frontier-only policy events.

## Coding rules applied
- Capability milestones M = METR frontier-setting releases (computed from out/horizons_*.csv); such releases are
  never also coded as visibility events.
- Events coded with LLM assistance from web sources (one link per event); no second human coder yet.
- Scheduled milestones (e.g. a law entering into force) are not events.

## Addendum: full run (written 2026-11-07T07:29:36Z, before any Trends or GDELT data were collected)
- Inputs: Wikipedia via the API (Artificial_intelligence, Machine_learning, ChatGPT, Large_language_model,
  AI_safety); Google Trends worldwide weekly (AI topic /m/0mkz, "ChatGPT", "AI agent"); GDELT DOC daily share of
  English-language articles per million monitored ("artificial intelligence", "chatgpt", "ai regulation" OR "ai safety").
- Same sample (weeks ending 2021-01-11 to 2026-09-28), same frozen events and analyze.py.
- Late-start rule: a series enters from the first week its weekly value reaches 25% of its median
  (reproduces the first run's Large_language_model start exactly).
- Main index: PC1 of the series present in every week; late starters enter only the equal-weight index.
- Primary outcomes as in the first run: A2 weeks 0-4 sums for V and M with permutation p; A3 weeks 0-4 sums;
  A4 excess, half-life and bootstrap IQR; ranks of the headline shocks among weekly rises.
- Code at freeze: attention.py sha256 fefa11605e7a339877baf9357d08226d063676c8043f15c2cd6ac45c838a26f0
                  scripts/run_attention.py sha256 360d4898d70be5428b6010368942a69ce1b27c6df537aa271b44520729d9768f
