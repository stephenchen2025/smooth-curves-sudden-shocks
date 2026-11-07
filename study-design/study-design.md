# Attention vs. Capability: Study Design for the Lag Analysis

Nov 6, 2026 · @Stephen

## 1. Aim and hypotheses

The study tests the paper's central claim with three linked series from 2019 to 2026: measured frontier capability, public attention, and policy events. The claim is that capability moves smoothly while attention and policy move in steps set by visibility. Each hypothesis below states what result would count against it.

| Hypothesis                        | Prediction                                                                                                                                 | Falsified if                                                                                        |
|-----------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| H1 · Continuity                   | The capability trend shows no level or slope break at the shock dates (Nov 30, 2022; Jan 20, 2025; Jul 21, 2026)                           | Models released after a shock sit significantly above the trend fitted on models released before it |
| H2 · Visibility drives attention  | Attention spikes follow visibility events (consumer launches, market moves, incidents), not capability milestones seen only in evaluations | Capability surprise predicts attention as well as visibility events do                              |
| H3 · Attention sets policy timing | Policy events follow attention spikes within weeks and are not predicted by capability surprise once attention is controlled for           | Capability surprise predicts policy events conditional on attention                                 |
| H4 · Decay                        | After a spike, the rate of policy events returns toward baseline while capability keeps rising                                             | Policy-event rates stay elevated in proportion to capability growth                                 |

Units: capability is observed per model release, attention weekly, and policy events daily and aggregated to weeks and months.

## 2. Data

Capability data is in hand from METR's public repository, and Wikipedia pageviews from a public copy of the Wikimedia data. Google Trends, GDELT and congress.gov need network access this workspace does not have, so their collectors are written and must be run on your machine. Policy and visibility events are coded and frozen (§3).

| Series                         | Source                                                                                                                                                                                     | Frequency                                 | Access                              | Status                                                 |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|-------------------------------------|--------------------------------------------------------|
| Agent time horizons (50%, 80%) | METR run-level data, Time Horizon 1.0 (33 models, 2019–2025) and 1.1 (20 models, 2023–Feb 2026) ([repo](https://github.com/METR/eval-analysis-public))                                     | Per model release                         | Public, Git                         | In hand; fits replicated                               |
| Capability index               | Epoch Capabilities Index and notable-models compute ([Epoch AI](https://epoch.ai/trends))                                                                                                  | Per model release                         | Public download                     | Download locally                                       |
| Search attention               | Google Trends via pytrends: "artificial intelligence" topic, "ChatGPT", "AI agent"                                                                                                         | Weekly, stitched from overlapping windows | Unofficial API                      | Collector written; run locally                         |
| Encyclopedia attention         | Wikimedia pageviews: Artificial intelligence and Machine learning (2021–), Large language model (2023–); first run from a CC0 copy of the API data on Hugging Face                         | Daily from 2015                           | Public REST API                     | In hand to Oct 2, 2026; rerun the collector to confirm |
| News attention                 | GDELT GKG article counts mentioning AI terms                                                                                                                                               | Daily                                     | BigQuery (gdelt-bq.gdeltv2.gkg)     | Query written; run locally                             |
| Legislative attention          | Congress.gov bills mentioning "artificial intelligence"; MultiState annual state counts ([MultiState](https://www.multistate.ai/artificial-intelligence-ai-legislation))                   | Daily / annual                            | CSV export from congress.gov search | Export by hand; loader written                         |
| Policy events                  | Hand-coded: bills, hearings, executive actions, rules, agreements, open letters                                                                                                            | Daily                                     | Coding manual in §3                 | 43 sourced events, frozen Nov 7, 2026                  |
| Visibility events              | Hand-coded: consumer launches, market moves, incidents                                                                                                                                     | Daily                                     | Coding manual in §3                 | 20 sourced events, frozen Nov 7, 2026                  |
| Survey validation              | Pew "more concerned than excited" series ([Pew, 2023](https://www.pewresearch.org/short-reads/2023/08/28/growing-public-concern-about-the-role-of-artificial-intelligence-in-daily-life/)) | Irregular                                 | Public                              | Used only to validate the attention index              |

The public METR data ends with models released in February 2026, so the July 2026 intrusion cannot yet be tested on the capability side.

## 3. Measures

Three constructed variables carry the analysis: a weekly attention index, a real-time capability surprise, and coded event series. All are defined before the attention data is collected, so the definitions can be pre-registered.

**Attention index (A).** Each input series is averaged to weeks, log-transformed (log1p) and z-scored over the full sample. The index is the first principal component of the z-scores, rescaled to unit variance; the equal-weight mean and each series alone are robustness checks. As a validity check, the index must rise between the Pew waves of December 2022 and August 2023, when concern moved from 38% to 52%.

**Attention spike.** A week in which the change in A exceeds two standard deviations of weekly changes. Only the first week of a run counts, and spikes must be at least eight weeks apart.

**Capability milestone (M) and surprise (S).** A milestone is a release that beats every earlier model's 50% horizon in the same METR suite (Time Horizon 1.0 through November 2025, 1.1 afterwards). Its surprise is its log2 horizon minus the trend fitted on all earlier milestones, in doublings. Only earlier data enters each fit, so S is what a forecaster watching the evaluations would have called unexpected at the time.

**Events (P for policy, V for visibility).** Each event gets a date (first public day), class, type, jurisdiction and scope:

- **Policy types:** bill introduced or announced, hearing, executive action, enforcement, legislative position, international agreement, open letter with 100 or more named signatories, and a developer's announced change to development pace.

- **Visibility types:** consumer launch, model release, market move, incident. A candidate counts only if it reaches at least three major outlets within 48 hours, checked against the news series.

- **Scope:** frontier capability, a specific app, or AI in general. The main tests use all policy events; a frontier-only subset is a robustness check.

- **Reliability:** two coders code a random 20% sample and report Cohen's κ. If an LLM assists with coding, that is disclosed and validated against the human codes.

The frozen list (data/events.csv, SHA-256 2fa44eeb…) holds 43 policy and 20 visibility events from April 2021 to September 2026, each with a source link. It was hashed on November 7, 2026, before the AI pageview series was opened. Coding was LLM-assisted from web sources and has not yet had a second human coder. METR frontier-setting releases count only as milestones, never also as visibility events.

## 4. Analyses

Four analyses map one-to-one onto the hypotheses. A1 is run (§5). A2 to A4 are checked on simulated data and have a first run on Wikipedia pageviews only (§6); they still wait for the search and news series.

**A1 · Capability breaks (H1).** For each shock date s, three tests on log2 of the 50% horizon against release date: an out-of-sample prediction test (fit on models before s, test those released in the following 18 months); a Chow-style F test for a level shift plus slope change at s, requiring at least five models on each side; and a placebo scan that runs the same F test at every month-start and reports the share of months whose statistic is at least as large as the shock's. A break that matters for H1 must be specific to the shock date, not just present somewhere.

**A2 · What moves attention (H2).** Local projections of attention on visibility weeks V and capability-milestone weeks M, with two lags of weekly attention changes:

A\_{t+h} - A\_{t-1} = \alpha_h + \beta_h V_t + \gamma_h M_t + \sum\_{k=1}^{2} \delta\_{h,k}\\ \Delta A\_{t-k} + \varepsilon\_{t+h}, \qquad h = -4, \dots, 12

H2 predicts β_h \> 0 and γ_h ≈ 0. The leads (h \< 0) test for pre-trends.

**A3 · What times policy (H3).** Poisson local projections of weekly policy events on attention changes and capability surprise, with lagged events and a linear trend:

\log \mathbb{E}\[P\_{t+h}\] = a_h + \theta_h\\ \Delta A_t + \phi_h S_t + \sum\_{k=1}^{2} \rho\_{h,k} P\_{t-k} + \tau_h t, \qquad h = 0, \dots, 12

H3 predicts θ_h \> 0 over the first weeks and φ_h ≈ 0 once attention is controlled for.

**A4 · Decay (H4).** Pooled over attention spikes, policy events in the k weeks after each spike, against that spike's baseline rate b over the previous 26 weeks:

\log \mathbb{E}\[P_k\] = \log b + a + c\\ r^{k}, \qquad \text{half-life} = \ln 2 / (-\ln r)

r is chosen by profile likelihood. H4 predicts a half-life of weeks to months, while capability keeps doubling every four to seven months.

**Inference.** Newey–West errors for all local projections. Because there are few large shocks, the main p-values come from permutation tests that circularly shift the event weeks, which preserves their spacing.

**Simulation check.** The code plants known effects in a simulated 400-week world and tries to recover them. The results below set realistic expectations for power.

| Quantity                                      | Planted   | Recovered                             |
|-----------------------------------------------|-----------|---------------------------------------|
| A2 · attention response to visibility, week 0 | 1.5       | 1.39; permutation p \< 0.005          |
| A2 · attention response to milestones, week 0 | 0         | −0.03; permutation p = 0.15           |
| A2 · largest pre-trend coefficient            | 0         | 0.01                                  |
| A3 · policy response to capability surprise   | 0         | mean −0.06, SD 0.38 over 15 seeds     |
| A4 · half-life of excess policy activity      | 4.3 weeks | median 2.8, IQR 2.1–5.2 over 15 seeds |

Two cautions follow. A3's attention coefficient is an impulse response, not the structural parameter, so read its sign and timing rather than its size. A4 is noisy and leans toward shorter half-lives, so report its interval rather than the point estimate.

## 5. Preliminary result: no capability break at the shock dates

On METR's run-level data, neither testable shock date marks a capability break. The evidence for a slope change is strongest in mid-to-late 2024, months before DeepSeek-R1, and weak by its release; the pre-2023 record is too thin to test ChatGPT cleanly.

**Replication.** Refitting each model with METR's headline method reproduces the published horizons: across 48 model–suite pairs, log horizons correlate at 0.999 with METR's values, with a median gap of 0.06 doublings. Full-sample doubling times are 6.8 months for Time Horizon 1.0 (95% CI 6.1–7.8) and 4.1 months for 1.1 (3.6–4.7), in line with METR's own seven-month and 4.3-month estimates.

**Table 1. Break tests at the shock dates.**

| Suite | Sample (models) | Shock       | Post-shock models vs pre-shock trend (doublings) | Prediction-test p | Break-test p          | Placebo months with a statistic at least as large |
|-------|-----------------|-------------|--------------------------------------------------|-------------------|-----------------------|---------------------------------------------------|
| 1.1   | Frontier (14)   | DeepSeek-R1 | +1.8                                             | 0.36              | 0.02                  | 36%                                               |
| 1.1   | All (20)        | DeepSeek-R1 | +1.8                                             | 0.76              | 0.05                  | 39%                                               |
| 1.0   | Frontier (17)   | DeepSeek-R1 | +0.9                                             | 0.46              | 0.03                  | 75%                                               |
| 1.0   | All (33)        | DeepSeek-R1 | +1.1                                             | 0.55              | 0.02                  | 67%                                               |
| 1.0   | Frontier (17)   | ChatGPT     | +2.0                                             | 0.02              | too few models before | —                                                 |
| 1.0   | All (33)        | ChatGPT     | +1.7                                             | 0.03              | too few models before | —                                                 |

<img src="media/image1.png" style="width:6in;height:2.74107in" alt="Computed from METR&#39;s public run-level data (Time Horizon 1.0 and 1.1), refitted with METR&#39;s headline method · candidate months need at least five models on each side" />

Computed from METR's public run-level data (Time Horizon 1.0 and 1.1), refitted with METR's headline method · candidate months need at least five models on each side

Each line moves from strong evidence of a break in mid-2024 to none by mid-2025; the shock date sits on the downslope, not at a peak.

Three findings follow:

- **DeepSeek-R1.** Models released in the 18 months after the shock sit 0.9–1.8 doublings above the pre-shock trend, but not significantly. The break tests at the shock date reach p = 0.02–0.05, yet 36–75% of arbitrary months give a statistic at least as large, so the break is not specific to the shock. The steepening it picks up is visible in evaluations from the first reasoning models onward, before the public reaction.

- **ChatGPT.** Only three models predate the launch, too few for the break test. Models released afterwards sit 1.7–2.0 doublings above the line through those three (p = 0.02–0.03), driven by GPT-4 in March 2023. On the full 2019–2025 trend, though, GPT-3.5 sits 0.8 doublings below and GPT-4 0.8 above, inside the model-to-model scatter (residual SD 0.9 doublings).

- **July 2026 intrusion.** Not testable yet: the public runs end with models released in February 2026.

**Implication for the paper.** The continuity claim holds against the full trend and at the DeepSeek date. §1 and §4.1 should, however, acknowledge that GPT-4, four months after ChatGPT, landed above the pre-2022 pace; the honest claim is that the shock date itself carried no capability jump, not that the period was jump-free.

## 6. First attention run: Wikipedia pageviews only

On Wikipedia pageviews, the only attention series reachable so far, none of the pre-registered tests finds an effect. The series also fails the checks that would make a null result informative, so this run leaves H2–H4 untested rather than refuted.

**Data.** Daily user pageviews for the English articles Artificial intelligence and Machine learning from January 2021 to October 2, 2026, and for Large language model from March 2023, when the article was created. The Wikimedia API, Google Trends and GDELT were unreachable from the workspace. The pageviews came instead from a CC0 copy of the Wikimedia API data on Hugging Face, rebuilt from overlapping windows; all 652 overlapping days agreed exactly. The event list and analysis plan were hashed and frozen before the AI series was opened. The main index is the first principal component of the two complete series (64% of variance) over 299 weeks, with 20 visibility events, 43 policy events and 16 capability milestones in the sample.

**Table 2. Pre-registered tests on the main index.**

| Test                                                                 | Estimate             | Permutation p |
|----------------------------------------------------------------------|----------------------|---------------|
| A2 · attention after visibility events, weeks 0–4 summed (index SD)  | +0.33                | 0.50          |
| A2 · attention after capability milestones, weeks 0–4 summed         | −0.19                | 0.70          |
| A2 · largest pre-trend coefficient, visibility / milestones          | 0.00 / 0.07          | —             |
| A3 · policy events on attention changes, weeks 0–4 summed (log rate) | +1.20                | 0.18          |
| A3 · policy events on capability surprise, weeks 0–4 summed          | +0.74                | 0.86          |
| A4 · excess policy rate after attention spikes (6 spikes)            | negative (−3.4, log) | 0.76          |
| A4 · half-life of the excess, bootstrap IQR over spikes              | 2.3–34 weeks         | —             |

The A2 signs go the way H2 predicts: up after visibility events, flat after milestones. The estimates are small against their noise, though. No specification in the robustness grid changes the conclusion: four index variants, one to four lags, frontier-only policy events and spike thresholds of 1.5–2.5 SD. A4's fit is unstable throughout, with half-lives from under one week to 69 weeks. With frontier-only policy events, A3's surprise term cannot be estimated.

**Why the null result says little.** Three checks show the index tracks something other than public attention to AI:

- It barely registers the visibility shocks the study is about. The ChatGPT launch week ranks 80th of 298 weekly rises and GPT-4's 106th, and attention fell in the week of the July 2026 intrusion. Among the ten largest rises, only the weeks of the AI Nobel prizes (October 2024) and DeepSeek-R1 (January 2025) line up with a named event.

- The school calendar explains 30% of weekly changes, which fits a readership made up mostly of students. The two articles correlate only 0.28 week to week.

- The largest rises are one-off surges with no event in the coded list (July 2021, March 2026). They look like changes in search referrals or automated traffic; the data cannot tell which.

The index does pass the Pew check, weakly: it is higher in August 2023 than in December 2022 (1.11 vs 0.95 SD).

**Exploratory, not pre-registered.** Adding the Large language model article (an equal-weight index from March 2023) raises the week-0 response to visibility events to 0.21 SD (SE 0.07). It also raises the weeks 0–4 sum to 0.88 (permutation p = 0.09), while milestones stay near zero (−0.23, p = 0.66). Removing week-of-year means from the main index does not help (p = 0.68). The newer, more specific article may track public attention better than the older encyclopedic ones. That is a hypothesis for the full run, not a result.

**Implication.** The paper should not cite this run as support for H2–H4. What it shows is that Wikipedia pageviews cannot carry the attention measure on their own. That makes Google Trends and GDELT necessary rather than optional, and argues for building the index from terms tied to current AI products and events.

## 7. Threats to validity and robustness checks

The weakest links are what the attention index measures and how few large shocks there are; each threat below has a planned check.

| Threat                            | What could go wrong                                                                                              | Planned check                                                                                                     |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| Attention construct               | Search and pageviews track product use and curiosity, not concern; "ChatGPT" searches measure the product itself | Concern-specific terms ("AI regulation", "AI safety") as a sub-index; Pew waves as validation; each series alone  |
| Series artefacts                  | Google Trends rescales and samples each request; news coverage in GDELT drifts                                   | Pull each Trends window several times and average; normalise GDELT counts by total daily articles                 |
| Capability scope                  | METR covers software and agentic tasks only; suites differ between versions; cheating can inflate scores         | Repeat A1 with Epoch's capability index; run each suite separately; drop models with flagged cheating             |
| Few large shocks                  | Three headline shocks cannot support inference alone                                                             | A2–A4 use the full coded event list; permutation p-values; the headline shocks reported descriptively             |
| Reverse causality and confounding | Hearings create coverage; legislative calendars and elections drive both series                                  | Leads in A2 and A3; legislative-session and election-week controls                                                |
| Researcher choices                | Thresholds, windows and index variants can be tuned to a result                                                  | Pre-register all of them; report a multiverse over spike threshold (1.5, 2, 2.5 SD), lags (1–4) and index variant |
| Selection of shocks               | The three cases were chosen because they were salient                                                            | Treat them as illustrations; base claims on the pre-registered event list                                         |

## 8. Running the code and next steps

The capability side is done and reproducible; the attention side runs on your machine in about an hour of setup plus Google Trends' rate limits. The code package (attention-capability-study.zip) holds:

| File                 | Purpose                                                                    | Status                                                                  |
|----------------------|----------------------------------------------------------------------------|-------------------------------------------------------------------------|
| capability.py        | Refits METR horizons per model from run-level data                         | Run; outputs in out/                                                    |
| breaks.py            | A1: prediction test, break test, placebo scan                              | Run; outputs in out/                                                    |
| attention.py         | Wikipedia and Google Trends collectors, GDELT BigQuery query, weekly index | Index tested on placeholder data; collectors untested (no network here) |
| analyze.py           | A2–A4 with permutation tests; --simulate self-check                        | Self-check passes; full pipeline smoke-tested end to end                |
| data/events_seed.csv | 17 policy and 5 visibility events with sources                             | Seed only; extend and freeze                                            |

The README has the exact commands. Before running the GDELT query, do a dry run: the GKG tables are large and a full scan is expensive.

**Next steps, in order:**

- [ ] Run ./run_local.sh: it collects Wikipedia, GDELT (free DOC API) and Google Trends, checks the mirrored pageviews, and runs A2–A4 under the full-run rules pre-registered in data/FREEZE.md

- [ ] Export the congress.gov bill search and add it to the inputs

- [ ] Have a second coder code 20% of the frozen event list (extended to 63 events on Nov 7)

- [ ] Pre-register measures, event list, windows and thresholds (OSF) before running A2–A4

- [ ] Run analyze.py, then the multiverse checks in §6

- [ ] Rewrite the paper around the results, starting with the GPT-4 caveat from §5

- [ ] Re-run A1 when METR publishes runs for models released after February 2026

## Sources

- METR. [eval-analysis-public](https://github.com/METR/eval-analysis-public): run-level data for Time Horizon 1.0 and 1.1, release dates and fitting code (cloned November 6, 2026).

- METR published horizons, as tabulated in [Wikipedia: METR](https://en.wikipedia.org/wiki/METR), used only for the replication check.

- Epoch AI. [Trends in AI](https://epoch.ai/trends).

- Pew Research Center (2023). [Growing public concern about the role of artificial intelligence in daily life](https://www.pewresearch.org/short-reads/2023/08/28/growing-public-concern-about-the-role-of-artificial-intelligence-in-daily-life/).

- MultiState. [State AI legislation tracker](https://www.multistate.ai/artificial-intelligence-ai-legislation).

- itsalissonsilva. [wikimedia-pageviews-forecasting](https://huggingface.co/datasets/itsalissonsilva/wikimedia-pageviews-forecasting) (Hugging Face, CC0): daily Wikipedia user pageviews from the Wikimedia API, retrieved October 31, 2026.

- Event sources: one link per event in data/events_seed.csv.
