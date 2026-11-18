# Presentation and viva prep: Rishabh Yadav

**Project:** Fair Mortgage Approval Decisions (Group 8, CSE3105)  
**Your part:** slides 11-15: fairness, recommendations, limits

> **How to use this file.** Read **Part 1** (the whole project) first so you can answer anything. Then read **Part 2** (your own slides) until you can present them without looking and answer every question listed. Part 3 is a short list of questions you may get on other people's slides.
>
> Repository: https://github.com/Rishhhhub/fair-mortgage-approval. Slides: `Group_8_Fair_Mortgage_Approval_Decisions_Presentation_v3.pptx` (the version with the thought-process lines).

---

## Who presents which slides

| Presenter | Slides | Topics |
|---|---|---|
| **Kanishk Chahar** | 1-6 | Title, problem, hypotheses as questions, data sources and the single table, questions while building the data, missing data |
| **Rishabh Kumar** | 7-10 | DTI and the 43% rule (H1), race gap (H2), area, rates and lender type (H3, H4, H7), the model and its drivers (H5) |
| **Rishabh Yadav** | 11-15 | Fairness (H6), scorecard, recommendations and demo, limits and next steps, conclusions |

Slides 16-18 are references and two appendix slides (use them to answer questions). The footer of each slide shows who presents it.

---

# Part 1. The whole project (read this first)

## A0. Our thought process: the questions we asked and how we answered them

The teacher likes to see how we thought. Every slide has a line "We asked: ..." and this is the full chain. Know it in order; it is also a good story to tell if you are asked "how did you approach this?".

| # | Question that came to mind | What we did | Where it shows |
|---|---|---|---|
| 1 | What decision is the lender actually trying to make, and what goes wrong today? | Took the credit-risk team's view: approve or deny, and under what rule, safe and fair. | Slide 2 |
| 2 | What do we need to find out? | Turned the problem into seven questions (H1-H7) and fixed the decision rule for each before looking. | Slide 3 |
| 3 | Which free public data can answer them? | HMDA (loans), Census ACS (area), FRED (rates, CPI), Reporter Panel (lender type), joined into one table. | Slide 4 |
| 4 | Can we use every HMDA row? | No, it is millions per year. Fixed 5% random sample per state-year, seeded, logged: 1.32 million rows. | Slide 5 |
| 5 | Do the sources actually join? | Census tracts changed in 2020: match was 68% for 2020-21. Mapped to ACS 2019: 98.4%. | Slide 5 |
| 6 | Does any column give away the answer? | Interest rate, fees exist only for approved loans (leakage). Excluded them. | Slide 5, Appendix A |
| 7 | What about extreme and missing values? | Capped extremes (kept originals). Missing is informative: 44% vs 9% denied, so we judge on complete cases. | Slides 5-6 |
| 8 | Is 43% really a cliff, or just a convention? | Regression discontinuity with fake-cutoff checks: no jump at 43; real jumps at 50%+. H1 not supported. | Slide 7 |
| 9 | Are similar applicants treated differently by race? | Logistic regression and propensity matching agree: 4.7 points (odds ratio 1.73). Association, not proof. | Slide 8 |
| 10 | Do the area, the interest rate and the lender type matter? | Small area gap (1.2 pts); non-banks deny 5.2 pts less; rates inconclusive (6 data points). | Slide 9 |
| 11 | Can many variables beat one rule, and what drives them? | LightGBM, trained 2018-22, tested on unseen 2023: AUC 0.825 vs 0.68. Drivers by SHAP. | Slide 10 |
| 12 | Is the model equally accurate for every group? | Fairness audit: one real gap (Asian false-negative rate +14.5 pts); Black-White gap small. | Slide 11 |
| 13 | So what did we actually learn? | Four supported, one not, two inconclusive. | Slide 12 |
| 14 | What should the lender do, and what can we not claim? | Graduated DTI scoring, explained triage, monitoring, pilot with credit scores. No credit score, associations only. | Slides 13-14 |

Two good "we changed our mind" stories (the pre-submission said we expected to change hypotheses):
- **H1:** we expected a jump at 43%. The data said no. We reported it as not supported and found the real jump at 50%+.
- **Credit history claim:** we first wrote that credit history was the main denial reason; checking the data showed DTI is (31.7% vs 28.3%), so we corrected it everywhere.


## A1. The project in one minute (memorise this)

A lender's credit-risk team decides which mortgage applications to approve. Today they use a fixed rule (debt-to-income below 43%) plus human judgement. If they deny good applicants they lose business; if they treat similar people differently by race or area they break fair-lending law.

We built one dataset of **1,320,227 US home-purchase applications (2018-2023, 99 columns)** from four public sources (HMDA loans, HMDA Reporter Panel, Census ACS, FRED). Using the BADIR framework we tested **seven hypotheses** with decision rules fixed in advance, built a **LightGBM model** that we explained with **SHAP** and audited for **fairness**, and wrote a **scoring API**.

**Headline results:** (1) there is **no cliff at 43% DTI**: denial rises gradually and jumps only at 50%+; (2) **gaps persist after comparing similar applicants**: Black applicants have 1.73 times the odds of denial (matched gap 4.7 points), low-income areas show a small gap, and non-bank lenders deny about 5 points less than banks; (3) the model reaches **AUC 0.825 on an unseen year** against 0.67 for the DTI rule; (4) it is a **triage tool, not an automatic decision-maker**, because HMDA has no credit score.

## A2. Problem, stakeholder and BADIR

- **Stakeholder:** the credit-risk team of a US home-loan lender. **Decision:** approve or not, and under what rule so that it is safe and fair.
- **BADIR:** **B**usiness question (what rule, is it fair?) -> **A**nalysis plan (each hypothesis mapped to a method and decision rule) -> **D**ata (acquire, clean, join into the SSOT) -> **I**nsights (EDA, tests, model, fairness) -> **R**ecommendation (graduated DTI scoring, explained triage API, fairness monitoring, pilot roadmap).
- **Teacher's three stages** (used in the slides): 1 Define the problem, 2 Validate the evidence, 3 Inform the decision.

## A3. The data

| Source | What we took | Joined on |
|---|---|---|
| **HMDA** (CFPB/FFIEC) | one row per application: outcome, income, loan amount, LTV, DTI, race, sex, age, lender ID, tract | base table |
| **Census ACS 5-year** | tract median household income, house value, poverty rate, unemployment rate | census tract + ACS year |
| **FRED** | 30-year mortgage rate (MORTGAGE30US), CPI (CPIAUCSL) | year |
| **HMDA Reporter Panel** | lender type (via `other_lender_code`, agency code, name) | lender ID (LEI) + year |

**Scope:** first-lien, owner-occupied, home-purchase applications that were **originated or denied** (withdrawn and not-accepted ones are excluded because there is no final decision).

**How we got HMDA (important to explain).** The CFPB API accepts at most **two filters**, and it needs a state. So `01_download.py` downloads **one state and one year at a time** (51 states x 6 years = 306 requests), filtering on loan purpose = purchase and action = originated or denied on the server. The remaining scope (first lien, owner-occupied) is applied locally. From each state-year we keep a **fixed 5% random sample** (seed = 42 + year). We sampled because the instructor said not to use all HMDA records (it would be many millions of rows). Every download is logged (rows downloaded, in scope, kept, date) in `sampling_log.csv`.

**Key numbers:** 1,320,227 rows, 99 columns; per year 213,875 / 219,896 / 242,691 / 257,792 / 213,413 / 172,560 (2018-2023); denial rate 13.0%.

**Joins and checks (`checked_merge` in `02_build_ssot.py`):** every join asserts the row count is unchanged and uses `validate="m:1"` so a duplicate key on the right cannot silently duplicate rows. Match rates: ACS 98.4% (97.8-98.9% by year), FRED 100%, Reporter Panel 99.8%.

**The tract-boundary trap.** Census tracts changed in 2020. HMDA 2018-2021 use 2010 tracts, 2022+ use 2020 tracts. When we joined HMDA 2020 to ACS 2020 the match was only 68%. We tested which ACS year matched each HMDA year (ACS 2018/2019 = 2010 tracts, ACS 2022/2023 = 2020 tracts) and now join HMDA 2020-21 to **ACS 2019**. Match rate went to 99%.

**Cleaning:** 21 duplicates dropped; `NA`/`Exempt` -> missing; income converted from thousands to dollars; income <= 0 set to missing (5,785 rows); LTV <= 0 or > 200 set to missing (122); extreme values **winsorized** at the 0.5th/99.5th percentile into new `*_w` columns (originals kept, 23,245 rows = 1.8% flagged); dollars converted to **2023 dollars** with CPI.

**DTI:** HMDA gives an exact value for 36-49 and ranges elsewhere (`<20%`, `20%-<30%`, ...). `dti_mid` = the exact value or the range midpoint; `dti_is_exact` flags the exact ones (48.2% of rows). 3.2% have no DTI.

**Missing data is informative.** Rows missing DTI, LTV or income have a **44% denial rate vs 9%** for complete rows: denied applications are often closed before underwriting. This is why we report **complete-case** results as the honest benchmark and run robustness checks keeping the incomplete rows.

**Parquet:** a compact column-based table file; stores types, about 10x smaller than CSV, read with `pd.read_parquet`.

## A4. Concepts you must be able to explain in plain words

- **DTI (debt-to-income):** monthly debt payments divided by monthly income. **LTV (loan-to-value):** loan amount divided by property value.
- **SSOT:** one consistent table built from several sources, with documented join keys, units, duplicate handling, missing-value treatment and checks.
- **Winsorizing:** pulling extreme values in to the 0.5th/99.5th percentile instead of deleting them, so a few absurd incomes (up to $846 million) cannot dominate results.
- **Data leakage:** using information the model would not have at decision time. Columns like `interest_rate`, `rate_spread`, fees and points exist **only for approved loans** (100% empty for denied), so a model using them would "predict" denial by noticing the column is empty. We excluded them. We also excluded action taken, denial reasons and purchaser type.
- **Complete-case vs all rows:** complete cases drop rows with missing DTI/LTV/income; all rows keep them with missing flags. We report both.
- **Regression discontinuity (RDD):** compare applicants just below and just above a threshold; they are nearly identical except for being on one side of the rule, so a jump in the outcome exactly at the threshold suggests the rule changes behaviour. We use exact DTI 43 vs 44 with a local linear model, clustered standard errors by state, and **placebo cutoffs** (fake thresholds 38-46) to see whether 43 stands out.
- **Linear probability model:** OLS on a 0/1 outcome; the coefficient is the change in probability (we use it for the RDD jump).
- **Logistic regression and odds ratio (OR):** models the log-odds of denial. OR = 1 means no difference; OR 1.73 means 73% higher odds of denial. We also report the **adjusted gap** in percentage points by predicting for everyone as if group = 1 vs 0 and averaging.
- **Propensity score matching (PSM):** the propensity score is the probability of being in the "treated" group (e.g. Black) given the observed financial profile and place. We pair each treated applicant with a control applicant (e.g. White) with a very similar score, then compare outcomes (the **ATT**). We use nearest-neighbour on the logit of the score with a **caliper** of 0.2 standard deviations, matching **with replacement**, and a **bootstrap** CI. **Balance check:** standardised mean differences should drop below 0.1 after matching.
- **Chi-square test:** tests whether two categorical variables are independent. With 1.3M rows everything is "significant", so **effect size and CI matter more than p-values**.
- **Gradient boosting (LightGBM):** many small decision trees added one after another, each correcting the errors of the previous ones. **Early stopping** stops adding trees when validation AUC stops improving. **Random search** tried 6 hyperparameter settings.
- **AUC/ROC:** the chance that a randomly chosen denied application gets a higher score than a randomly chosen approved one. 0.5 = coin flip, 1.0 = perfect.
- **Time-based split:** train on 2018-2022, test on 2023. This mimics real use (learn from the past, score the future) and avoids leaking the future.
- **Threshold (0.31):** the score above which we flag an application. Chosen on 2022 validation data by maximising F1, never on the test year.
- **Calibration:** whether a predicted 30% really means about 30% were denied. We checked with a reliability curve and an isotonic recalibration (Brier score unchanged: 0.0675).
- **SHAP:** assigns each feature a contribution to each prediction (from game theory). **Mean |SHAP|** is how much a feature moves predictions on average. We use LightGBM's built-in exact TreeSHAP (`pred_contrib=True`).
- **FPR / FNR:** **FPR** = share of *approved* applicants the model would deny; **FNR** = share of *denied* applicants the model would approve.
- **80% rule:** a group's approval rate should be at least 80% of the reference group's.
- **Reweighing (Kamiran & Calders):** weight each training example by `P(group)P(outcome)/P(group, outcome)` so group and outcome look independent; race is used only to compute weights, never as a model input.

## A5. Results, hypothesis by hypothesis

All tested at the 5% level with **decision rules fixed before looking at results**.

| # | Hypothesis | Rule | Result | Verdict |
|---|---|---|---|---|
| **H1** | Denials jump sharply above DTI 43% | RDD jump at 43 positive, significant and larger than every placebo | Jump **-0.50 pp** (CI -0.85 to -0.14, bandwidth +/-3); sign changes with bandwidth; placebo cutoffs 44 and 45 have larger positive jumps (+0.6, +0.8). By loan type: conventional -0.63, FHA -0.15, VA -0.73. Denial rises gradually (7.3% at DTI 36 to about 10% at 46-48); jumps at 50-60% (24%) and above 60% (88%). | **Not supported** |
| **H2** | Race gap remains for similar applicants | OR CI above 1 **and** matched gap CI above 0 | Raw (complete cases) 16.1% vs 7.7%. OR **1.73** (CI 1.65-1.82). Matching: Black 16.1% vs matched White 11.4%, gap **4.71 pp** (CI 4.39-5.01). All rows with missing flags: OR 1.76. | **Supported** (association) |
| **H3** | Low-income areas denied more | adjusted OR CI above 1 | Raw 12.0% vs 8.4%. Adjusted OR **1.17** (1.11-1.22), gap 1.2 pp, within the same state. All rows: 1.14. | **Supported** (small) |
| **H4** | Higher rates -> more denials, smaller loans | Inconclusive unless both correlations strong (p<0.01) | Rate vs adjusted denial r = 0.73 (p = 0.099); rate vs median loan r = 0.23 (p = 0.66). **Only 6 yearly points**, one national rate. | **Inconclusive** |
| **H5** | Model AUC > 0.80 and DTI, LTV matter most | complete-case AUC > 0.80 **and** both in top 3 by mean abs SHAP | AUC **0.825** (CI 0.821-0.830) passes. Top 3: preapproval, DTI, property value. LTV is 6th. | **Inconclusive** |
| **H6** | Error gaps by group > 5% | any group n>=1,000: error/FPR/FNR gap > 5 pp vs White with CI above 0 | Asian FNR 50.0% vs White 35.5% = **+14.5 pp**, stable across thresholds. Black-White error gap 4.2 pp (below 5). 15 comparisons, one significant. | **Supported** (one group) |
| **H7** | Non-banks differ from banks | OR CI excludes 1 **and** matched gap CI excludes 0 | Raw 8.1% vs 10.2%. OR **0.56** (0.52-0.61). Matched: 8.1% vs 13.3%, gap **-5.21 pp** (CI -5.30 to -5.11). | **Supported** (non-banks deny **less**) |

**Why H5 is "Inconclusive" (explain carefully):** the AUC half holds (0.825 > 0.80). The "DTI and LTV lead" half does not: the top features were `preapproval` (28.4%), DTI (18.4%), property value (14.2%), loan amount (7.5%), dwelling category (7.1%), LTV (5.9%). `preapproval` marks pre-approval *requests* (an application type, not a borrower trait). **Extra, post-hoc check:** without it, AUC 0.814 and the top 3 are DTI (25.9%), property value (19.8%), loan amount (10.2%); grouped by theme, leverage (DTI, LTV, loan-to-income) is the largest group (36.4% vs 32.9% for size). We kept the verdict as pre-registered.

**Why H6 is "Supported" but needs care:** the rule flags the Asian false-negative gap. But Black-White gaps are small (error gap 4.2 pp, approval ratio 0.89 > 0.80), we ran 15 comparisons, and the audit compares the model with historical decisions that may themselves be biased. Reweighing barely changed the gaps because the model never sees race (Black-White FPR gap 0.78 -> 0.65 pp; error gap 4.16 -> 4.25 pp; AUC 0.880 -> 0.879).

## A6. The model and the API

- **Features (17):** DTI, LTV, income, loan amount, property value, loan-to-income, loan term, units, tract income % of metro, ACS median household income (2023 $), ACS poverty rate, ACS unemployment rate, loan type, loan product, dwelling category, construction method, preapproval.
- **Deliberately NOT used:** race, ethnicity, sex, age (fair-lending law, used only to audit); tract minority share (near-proxy for race); all leakage columns.
- **Split:** train 2018-2021 (934,254 rows) for tuning, validate 2022, **final fit 2018-2022 (1,147,667 rows), test 2023 (172,560 rows)**. Chosen params: 63 leaves, min child samples 50, feature fraction 1.0, L2 5, learning rate 0.08, bagging 0.8, **305 trees**; validation AUC 0.8651.
- **Test results (2023):** AUC **0.880 all rows, 0.825 complete cases**, 0.927 on rows with missing DTI/LTV/income (that gap is the missing-data effect). PR-AUC 0.749 / 0.587. Brier 0.0675. At threshold 0.31 on complete cases: precision 72%, **recall 45%**, accuracy 92.5%.
- **Baselines (same rows):** DTI rule of thumb 0.668 (all) / 0.682 (complete); logistic regression 0.833 / 0.770.
- **API (`src/api.py`, FastAPI):** `POST /score` returns the denial probability, a recommendation ("REFER FOR MANUAL REVIEW" if probability >= 0.31, else "LOW DENIAL RISK") and the top 3 SHAP factors. `GET /health` returns model info. The input model has `extra="forbid"`, so any unknown field such as `race` returns an error (HTTP 422). Five automated tests pass (`python tests/test_api.py`).

## A7. Limitations: say these before they are asked

1. **No credit score and no repayment outcome** in HMDA. We study denial, not default. The model catches only about 45% of denials. Credit history is the primary reason in 28.3% of denials and the model cannot see it.
2. **Association, not causation**, except where the design helps (RDD). The race gap is *not proof of discrimination*.
3. **Past decisions may be biased**; the model learns them and the audit compares against them.
4. **Missing data is informative** (44% vs 9%), so complete-case AUC (0.825) is lower than all-rows AUC (0.880).
5. **H4 has six data points** and one national rate; it cannot separate rates from COVID or the refinance boom.
6. **Public HMDA data is rounded** (loan amounts and property values at round numbers, ages banded).
7. **5% sample** gives less precision for small groups. No house price index was added. The mortgage rate is national, not by state.
8. **Drift:** denial rate went from 12.7% (train) to 15.3% (2023).
9. Denial reasons (all denied applications): debt-to-income 31.7%, credit history 28.3%, collateral 10.6%, incomplete application 8.5%, other 7.3%, unverifiable information 6.7%, insufficient cash 4.0%, employment history 2.9%, mortgage insurance denied 0.1%.

## A8. Numbers cheat sheet

| Item | Value |
|---|---|
| Rows / columns | 1,320,227 / 99 |
| Years | 2018-2023 |
| Overall denial rate | 13.0% |
| Raw denial: Black / White / Asian | 23.8% / 11.3% / 10.3% (full sample) |
| Raw denial: low-income tracts / upper-income tracts | 18.6% / 8.8% |
| DTI 36 / 43 / 49 / 50-60% / above 60% denial | 7.3% / 8.2% / 9.1% / 23.9% / 87.7% |
| Exact-DTI rows used in the RDD | 636,043 |
| RDD jump at 43 | -0.50 pp (CI -0.85 to -0.14) |
| H2 odds ratio / matched gap | 1.73 / 4.71 pp |
| H3 odds ratio | 1.17 |
| H7 odds ratio / matched gap | 0.56 / -5.21 pp |
| Model AUC (complete / all rows) | 0.825 / 0.880 |
| DTI rule AUC | 0.668 |
| Threshold / recall / precision | 0.31 / 45% / 72% |
| Complete cases | 1,170,521 rows (88.7%) |
| Missing-data denial rate vs complete | 44% vs 9% |
| ACS / FRED / Panel match rates | 98.4% / 100% / 99.8% |
| Sample | 5% per state-year, seed 42 + year |

## A9. Likely questions and model answers (whole project)

**1. In one sentence, what did you do?** We built one dataset from four public sources, tested seven pre-specified hypotheses on what drives mortgage denial and whether there are unfair gaps, built an explainable model, audited it for fairness and wrote a scoring API.

**2. Why did you sample 5% instead of all the data?** The instructor asked us not to use all HMDA records (it is millions of rows per year). A fixed 5% random sample per state-year (seed 42 + year) gives 1.3M rows, above the 100,000-row minimum, and is reproducible and logged.

**3. Is the sample representative?** It is a simple random sample within each state-year, so it keeps the states' relative sizes. It is less precise for small groups (for example "Other / 2+ races" has about 2,000 test rows). We used 95% CIs and set a minimum group size of 1,000 for H6.

**4. Why not Apache Spark?** Your handout lists Spark, but our instructor told us to avoid it unless absolutely required. 1.3M rows fit comfortably in pandas, and the whole pipeline reruns in 15-20 minutes on a laptop.

**5. What is leakage and where did you find it?** Information the model would not have at decision time. `interest_rate`, `rate_spread`, fees and points exist only for approved loans (100% missing for denied), so using them would let the model cheat. We showed this in a table and excluded them.

**6. Why did you exclude race, sex and age from the model?** Fair-lending law (ECOA) forbids using them in decisions. We used race and sex only afterwards to audit the model, and the API rejects those fields.

**7. Why is the complete-case AUC lower than the all-rows AUC?** Rows missing DTI/LTV/income are mostly denials closed early, so "missing" is itself a strong hint (AUC 0.927 on those rows). The complete-case AUC, 0.825, is the honest number.

**8. Is the 4.7 point race gap proof of discrimination?** No. It is an association after controlling for observed finances and place. HMDA has no credit score, which strongly drives real decisions, so unobserved credit differences could explain part of it. It is a reason to investigate, not proof.

**9. Why did H1 fail? You expected a jump at 43%.** The pre-submission said we expected to change some hypotheses. The data show a gradual rise and no break at 43; the RDD jump is -0.5 pp and placebo cutoffs look similar or larger. The real jumps are at 50% and above. That is a useful finding for the lender: do not treat 43% as a cliff.

**10. Why did you call H4 "inconclusive"?** There are only six yearly data points and one national mortgage rate, so we cannot separate the effect of rates from COVID or the refinance boom. We reported the correlation (r = 0.73) honestly but said the design cannot settle it.

**11. Why is H5 inconclusive when AUC is above 0.80?** H5 had two parts. The AUC part passes. The part saying DTI and LTV are the most important features does not: LTV is sixth. The pre-approval flag is first. We kept the verdict set in advance and reported a post-hoc check that shows leverage variables are the largest group once the flag is removed.

**12. Is the model good?** It is solid for public data: AUC 0.825 on an unseen year against 0.67 for the DTI rule and 0.77 for logistic regression on the same rows. But recall is 45% because there is no credit score, so it is a triage tool.

**13. Could a loan officer use it to accept or reject people?** Not as an automatic decision. It was trained on past decisions, has no credit score, and would need fair-lending validation. The API recommends manual review for high scores and says it is decision support only. We propose a shadow pilot on the lender's own data first.

**14. How do you know the model does not overfit?** We tuned on 2022 (held out during tuning) and tested on 2023, a year the model never saw. On all rows the validation AUC was 0.865 (2022) and the test AUC 0.880 (2023), so there is no sign of overfitting; the lower 0.825 is the complete-case number, not a drop from overfitting.

**15. Why a time-based split instead of random?** Random splitting would let the model see the same years it is tested on. Training on the past and testing on the future mimics real use.

**16. How did you choose the threshold?** By maximising F1 on the 2022 validation predictions (0.31), not on the test year. A table in the report shows what other thresholds would do.

**17. What does SHAP tell you?** How much each feature moves each prediction. The top drivers were the pre-approval flag, DTI and property value. We used it both globally (mean absolute SHAP) and per applicant (the API's top 3 factors).

**18. What fairness problems did you find?** Raw and adjusted gaps in the data (H2, H3, H7). For the model: one significant error gap (Asian false-negative rate +14.5 pp), small Black-White gaps (error gap 4.2 pp, approval ratio 0.89). We tried reweighing, which barely changed anything because the model already excludes race.

**19. Did you use AI to write the code?** Yes, parts of the code and of the report were written with Claude Code, as approved by the instructor. This is disclosed in the README and the acknowledgements. We reviewed the work and each of us can explain the parts below.

**20. How would you reproduce your results?** Install requirements, get a Census API key, run `01_download.py` for HMDA/ACS/FRED, place the Reporter Panel files in `data/raw/panel/`, run `02_build_ssot.py`, then run the three notebooks in order. We did a clean rerun and got identical results.

**21. What would you do with more time or data?** Use the lender's own data with credit scores and repayment, model default and not only denial, add monthly and state-level data for H4, test other fairness criteria, and add drift monitoring.

**22. What is the single most important limitation?** No credit score. It limits both the model's recall and how far we can interpret any gap.

**23. Which hypothesis did you want to test but could not, and why?** H8: that credit score explains a large part of the Black-White denial gap. The public HMDA file only gives the *type* of credit score model, not the score, so we had the rows but not the key variable. With a lender's own data we would add the score to the H2 regression and matching and see how much the odds ratio of 1.73 shrinks. Partial evidence: 36.4% of denied Black applicants cite credit history as the primary reason, against 28.3% of White applicants.

**24. Why not use a dataset that has credit scores?** The public datasets we know of that include scores (the Freddie Mac and Fannie Mae loan datasets) only contain loans that were acquired, which means approved loans, so there are no denials to study. They would suit a default question instead (H9).

## A10. The hypothesis we wanted to test but could not (the teacher asked for this)

**H8 (not tested): After controlling for credit score, the Black-White gap in denial shrinks substantially.** In words: credit history explains a large part of the race gap we found in H2. Pre-specified rule we would use: *supported* if adding credit score cuts the adjusted log-odds of the Black coefficient by at least half and the remaining gap is smaller than in H2; *not supported* if the gap stays about the same.

**Why we wanted it.** H2 found an odds ratio of 1.73 (matched gap 4.7 pp), but we could only call it an *association*, because the main variable lenders use, the applicant's credit score, is missing. H8 asks the question that H2 leaves open: how much of the gap is credit history and how much is left unexplained.

**Why we could not test it: missing variable, not too few rows.** The public HMDA file does not contain the credit score. It only has `applicant_credit_score_type` (which scoring model was used, for example 1 = Equifax Beacon 5.0), not the score itself. As we understand it, the score is reported to regulators but not released in the public file (check the CFPB's HMDA data-point list before stating this as fact). So we have 1.3 million rows but no credit score for any of them.

**What data would be needed.** A lender's own application records (approved *and* denied) with credit scores, or restricted-access HMDA data. Public loan-level datasets that do include credit scores (for example the Freddie Mac and Fannie Mae loan datasets, which we believe are free with registration) contain only loans that were *acquired*, i.e. approved, so they cannot be used to study denial. They would suit the default question below.

**How we would test it.**
1. Re-fit the H2 logistic model and the matching with credit score added to the controls.
2. Compare the Black odds ratio before (1.73) and after; report the share of the log-odds gap explained.
3. Repeat the matching with credit score in the propensity model and check balance.
4. Run the same for H3 and H7, to see whether neighbourhood and lender-type gaps also shrink.

**Partial evidence we do have (not a test).** Among *denied* applicants, the primary reason given is credit history for **36.4% of Black applicants, 28.3% of White and 10.6% of Asian**. That is consistent with credit history explaining part of the Black-White gap, and with the Asian applicants' lower denial rate. It is only suggestive: it is the share *among denials* (not the denial rate among applicants), and the reasons are reported by the lenders.

**A second untestable hypothesis (also mention if asked for more).** *H9: loans approved with DTI above 43% default more often than those below.* This is the real justification for the 43% rule. H1 tested whether lenders *behave* differently at 43%, not whether the rule is *right*. HMDA has no repayment data, so we cannot test it. A loan-performance dataset (see above) would be needed.

## A11. Demo script (2 minutes): dashboard and API

1. In a terminal: `cd C:\Users\Thanua\fair_mortgage` then `python -m uvicorn src.api:app`. Leave it open.
2. Open **http://127.0.0.1:8000/** (the dashboard). Do this once before the viva and check it loads.
3. Press **Approved in the data** (Colorado, $385,000 loan, DTI 39%, a real 2023 HMDA application): the model says **APPROVE** (about 2.5% chance of denial) and the line "What really happened" shows the real outcome, approved, and "model agrees".
4. Press **Denied in the data** (Georgia, $325,000 loan, DTI 50-60%, entered as 55): the model says **DENY / REFER** (about 62%) and the real outcome is denied.
5. Say what the page says under the buttons: these are clear, typical cases from 2023, a year the model never saw; the model catches about 45% of real denials overall, so some real denials would show APPROVE.
6. Type your own numbers or press **Random application** to show it works live. Point out the top 3 reasons.
7. Optional: http://127.0.0.1:8000/docs shows the raw API; adding `"race": "x"` to a request returns an error, which is the fair-lending guarantee.

---

# Part 2. Your slides: 11 to 15 (Rishabh Yadav)

You present **fairness, the scorecard, the recommendations with the live demo, the limits and the conclusion**. You close the presentation and stay on screen during questions.

| Slide | Title | Time |
|---|---|---|
| 11 | Errors are similar across groups, except for Asian applicants | 75 s |
| 12 | Four hypotheses are supported, one is not, and two are inconclusive | 75 s |
| 13 | We recommend graduated DTI scoring, explained triage, and monitoring of group gaps (with the demo) | 120 s |
| 14 | The model is a triage tool: it has no credit score and needs a pilot on the lender's data | 60 s |
| 15 | Conclusions | 45 s |

## What to say, slide by slide

**Slide 11 (fairness, H6).** "Is the model equally accurate for every group? The chart shows the false-negative rate, the share of applications that were really denied but that the model would approve. For White applicants it is 35.5%; for Asian applicants it is 50%, a gap of 14.5 points. That is the one significant gap among 15 comparisons. The Black-White error gap is only 4.2 points, and the model's approval ratio for Black applicants is 0.89 of White applicants, above the 80% rule. So H6 is supported through one group. The model never sees race; we use it only to audit." *We asked: is the model equally accurate for every group?*

**Slide 12 (scorecard).** "Here is the whole picture. H1, the 43% jump, is not supported: minus 0.5 points against plus 0.6 and 0.8 at fake cutoffs. H2, the race gap, is supported: 4.7 points, odds ratio 1.73. H3 is supported but small. H4 is inconclusive with six data points. H5 is inconclusive: AUC is 0.825 but LTV is not in the top three. H6 is supported through the Asian false-negative gap. H7 is supported: non-banks deny 5.2 points less. Unsupported and inconclusive results are valid outcomes." *We asked: so what did we actually learn?*

**Slide 13 (recommendations and demo).** "Three recommendations, each from a finding. One: replace the hard 43% cutoff with graduated DTI scoring, because denial is 8% at 43 but 24% at 50 to 60 and 88% above 60. Two: use the model for explained triage, not automatic decisions. At score 0.31 the model flags 6.6% of applications and 72% of the flags are real denials. The 43% rule flags 40% of applications and only 16% are real denials. Three: monitor group gaps every month and alert above 5 points. Let me show it." Then the demo (see A11): press **Approved in the data**, then **Denied in the data**, say the model's verdict and the real outcome, then one custom input. *We asked: what should the lender do with this?*

**Slide 14 (limits and next steps).** "The model is a triage tool. It has no credit score, so recall is only 45%. Our findings are associations, not proof. The model learns past decisions, bias included. We also could not test whether credit score explains the race gap, because public HMDA gives only the score type. Next steps: a shadow pilot on the lender's data with credit scores, months 0 to 3; triage of borderline applications, months 3 to 6; monitoring of group gaps under 5 points, months 6 to 12." *We asked: what can we not claim?*

**Slide 15 (conclusions).** "To close: no cliff at 43%, risk rises from 50%; gaps persist after controls, race 4.7 points; a usable prototype with AUC 0.83 against 0.68, for triage not automatic decisions. Our ask is a shadow pilot on your own data with credit scores. All code, notebooks and the model are on GitHub. We are happy to take questions." Leave this slide on the screen.

## Concepts you must master

- **False-negative rate (FNR):** among applications that were really denied, the share the model would approve. **False-positive rate (FPR):** among approved ones, the share the model would deny. **Error rate:** share wrong overall.
- **Gap vs White with a 95% CI:** each group's rate minus the White rate; only gaps above 5 points with a CI above zero and at least 1,000 rows count for H6.
- **Multiple comparisons:** we ran 15 comparisons (5 groups x 3 metrics); one was significant, so treat it with care.
- **80% rule:** a group's approval rate should be at least 80% of the reference group's (0.89 here).
- **Reweighing (Kamiran and Calders):** weights each training example so group and outcome look independent; race is used only to compute weights. It barely changed anything because the model never sees race (Black-White error gap 4.16 -> 4.25 pts).
- **Why audit with race but not train with it:** fair-lending law (ECOA) forbids using race in decisions; auditing needs it to measure gaps.
- **Threshold 0.31:** chosen on 2022 by maximising F1; at 0.31 on 2023 it flags 6.6% of applications with 72% precision and 45% recall. The 43% DTI rule flags 40% with 16% precision and 62% recall (it catches more denials but wrongly flags far more people).
- **Triage vs automatic decision:** the model sorts applications for review; a human decides.
- **Shadow pilot:** run the model beside the real process without changing any decision, to measure it on the lender's own data.
- **Decision support only:** the API and dashboard say so.

## Numbers to know cold

Asian FNR 50.0% vs White 35.5% (+14.5 pts), the only significant gap among 15; Black-White error gap 4.2 pts; approval ratio 0.89; scorecard 4 supported / 1 not / 2 inconclusive; model at 0.31: flags 6.6%, precision 72%, recall 45%; 43% rule: flags 40%, precision 16%, recall 62% (2023 complete cases, range midpoints for DTI); alert level 5 pts; roadmap 0-3 / 3-6 / 6-12 months; AUC 0.825 vs 0.68; DTI 8% at 43, 24% at 50-60, 88% above 60; API: POST /score, extra fields rejected, 5 tests pass.

## Code you must know

### Code walkthrough: `03_model_fairness.ipynb` (fairness audit)
- **Fairness:** `fairness_table()` computes per-group n, actual and predicted denial rate, error rate, FPR, FNR and the gap vs White with a normal-approximation 95% CI (`diff_ci`). H6 flags any gap above 5 pp with CI above 0 for groups with n >= 1,000. Also the 80% approval-ratio rule and a **threshold sweep** (0.20-0.50).
- **Mitigation:** Kamiran-Calders **reweighing** weights, retrain, recompute gaps.
- **Saving:** `lgbm_denial.txt` (the model) and `model_card.json` (features, categories, threshold, AUC, medians, exclusions); also updates `hypothesis_results.csv` for H5/H6.

### Code walkthrough: `src/api.py`
- Loads `models/lgbm_denial.txt` and `model_card.json` once at start-up.
- **`Application`** (Pydantic): the fields the model needs, with units and defaults; `extra="forbid"` rejects any unknown field (race, sex, age, ethnicity -> HTTP 422); `loan_amount_w` is required and must be positive.
- **`to_frame()`**: computes `loan_to_income` the same way as the build script, builds categorical columns with the **same categories as training**, converts numeric fields.
- **`POST /score`**: predicts the probability, computes the top 3 SHAP factors with `pred_contrib=True`, returns probability, recommendation (threshold 0.31), factors and a "decision support only" note. **`GET /health`**: model information.
- **`tests/test_api.py`** (5 tests): health; low-risk vs high-risk ordering; missing fields accepted; bad input rejected; protected attributes rejected.

### Recommendations (BADIR "R")
1. **Replace the hard 43% cut-off with graduated DTI scoring;** focus review at 50%+ (24% then 88% denied).
2. **Use the model for explained triage, not automatic decisions;** high-risk applications go to a human.
3. **Monitor group gaps monthly** (by race group and lender type); alert above 5 pp.
4. **Pilot on the lender's own data with credit scores** (shadow mode first).

**Roadmap (proposed):** Phase 1 shadow pilot, months 0-3, AUC >= 0.80 on their data and no decisions changed; Phase 2 triage of borderline applications, months 3-6, review hours per file and false-positive rate; Phase 3 monitoring and policy review, months 6-12, group gaps under 5 pp and drift alerts.

## Your demo (same as A11 in Part 1)

1. In a terminal: `cd C:\Users\Thanua\fair_mortgage` then `python -m uvicorn src.api:app`. Leave it open.
2. Open **http://127.0.0.1:8000/** (the dashboard). Do this once before the viva and check it loads.
3. Press **Approved in the data** (Colorado, $385,000 loan, DTI 39%, a real 2023 HMDA application): the model says **APPROVE** (about 2.5% chance of denial) and the line "What really happened" shows the real outcome, approved, and "model agrees".
4. Press **Denied in the data** (Georgia, $325,000 loan, DTI 50-60%, entered as 55): the model says **DENY / REFER** (about 62%) and the real outcome is denied.
5. Say what the page says under the buttons: these are clear, typical cases from 2023, a year the model never saw; the model catches about 45% of real denials overall, so some real denials would show APPROVE.
6. Type your own numbers or press **Random application** to show it works live. Point out the top 3 reasons.
7. Optional: http://127.0.0.1:8000/docs shows the raw API; adding `"race": "x"` to a request returns an error, which is the fair-lending guarantee.


## Questions on your slides (practise answering out loud)

1. **What does a false-negative rate of 50% mean?** Of the Asian applicants who were really denied, the model would approve half, against 35.5% for White applicants.
2. **Why is that gap not a big problem for Black applicants?** The Black-White error gap is 4.2 points, below the 5-point rule, and the approval ratio is 0.89, above 0.80.
3. **You ran 15 comparisons and found one. Is it real?** It is stable across thresholds (0.20 to 0.50), but with 15 comparisons one can appear by chance; we flag it for monitoring rather than claim a conclusion.
4. **Why did reweighing not change anything?** The model never sees race, so there was little group dependence to remove.
5. **Why not use race in the model if it improves fairness checks?** Fair-lending law forbids it; we use race and sex only to audit.
6. **Is the model fair?** Reasonably so on the metrics we checked, with one gap to monitor. It also learns historical decisions, which may themselves be biased, so we say it needs a pilot and monitoring.
7. **Why is H6 "supported" while the Black-White gap is small?** The rule asked for any group with a gap above 5 points and a CI above zero; the Asian false-negative rate meets it.
8. **Walk me through the scorecard.** 4 supported (H2, H3, H6, H7), 1 not supported (H1), 2 inconclusive (H4, H5).
9. **Why are inconclusive and not-supported results fine?** The guidelines say so, and reporting them honestly is better than forcing a conclusion.
10. **How does each recommendation follow from a finding?** No cliff at 43% -> graduated scoring; model beats the rule but has limits -> triage; persistent gaps -> monitoring; no credit score -> pilot with credit scores.
11. **The model flags 6.6% and the rule flags 40%. Which is better?** Different trade-offs. The rule catches 62% of denials but 84% of its flags are wrong; the model catches 45% and 72% of its flags are right. For triage, precision matters because human review time is costly.
12. **Can a loan officer use it to accept or reject?** Not automatically. No credit score, trained on past decisions, needs fair-lending validation. The page says "DENY / REFER": high risk goes to a human.
13. **How do you stop the API using race?** The model has no race input, and the API schema rejects unknown fields with an error (tested).
14. **What did the demo show?** A real approved 2023 application (model approves) and a real denied one (model flags); the page tells you that the model catches only about 45% of denials, so some real denials show APPROVE.
15. **What is the success indicator of the pilot?** AUC at least 0.80 on the lender's data, review hours per file, false-positive rate, group gaps under 5 points, drift alerts.
16. **What could not be tested?** H8: does credit score explain the race gap? Public HMDA has only the score type, not the score. We would add it to the H2 regression and see how much the odds ratio 1.73 shrinks.
17. **Did you use AI?** Yes, with the instructor's approval, disclosed in the README and the report; each of us can explain our parts.
18. **What do you ask the lender to do?** Run a shadow pilot on their own data with credit scores.

## Your thought-process story (if asked "how did you reach the recommendation?")

"We asked what the lender could actually do differently. The 43% rule: the data say no cliff, so use graduated scoring. The model: it beats the rule, but without credit scores it misses more than half the denials, so it should sort and explain, not decide. The gaps: they persist, so monitor them every month. And since we cannot see credit scores, the honest next step is a pilot on the lender's own data."

## Part 3. Quick answers for questions on other people's slides

- **What is the project in one sentence?** We built one dataset from four public sources, tested seven pre-set hypotheses about what drives mortgage denial and whether there are unfair gaps, built an explainable model, audited it for fairness and wrote a scoring API and dashboard.
- **Headline results?** No cliff at 43% DTI (denial rises gradually, jumps from 50%); gaps persist after comparing similar applicants (race 4.7 pts, odds ratio 1.73); model AUC 0.825 on unseen 2023 vs 0.68 for the DTI rule; it is a triage tool because HMDA has no credit score.
- **Scorecard?** Supported: H2, H3, H6, H7. Not supported: H1. Inconclusive: H4, H5.
- **Biggest limitation?** No credit score (recall only 45%) and findings are associations.
- **Which hypothesis could you not test?** H8: does credit score explain the race gap? Public HMDA has only the score type, not the score.
- **Did you use AI?** Yes, with the instructor's approval; it is disclosed in the README and report, and each of us can explain our parts.
