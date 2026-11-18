# Presentation and viva prep: Kanishk Chahar

**Project:** Fair Mortgage Approval Decisions (Group 8, CSE3105)  
**Your part:** slides 1-6: problem, hypotheses, data

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

# Part 2. Your slides: 1 to 6 (Kanishk Chahar)

You open the presentation and own **Stage 1 (Define the problem)** plus the data-quality slide. Your job: make the teacher understand the problem, the questions and why the data can be trusted.

| Slide | Title | Time |
|---|---|---|
| 1 | Title | 20 s |
| 2 | Lenders need to know what drives denial, and whether a fixed 43% DTI rule is fair | 60 s |
| 3 | We turned the problem into seven questions, each judged by a rule fixed in advance | 75 s |
| 4 | Four public sources are joined into one table, far above the required size | 75 s |
| 5 | Questions that came up while building the data, and how we solved them | 90 s |
| 6 | Missing data is informative, so the model is judged on complete cases | 75 s |

## What to say, slide by slide

**Slide 1 (title).** "Good morning. We are Group 8 and our project is Fair Mortgage Approval Decisions. We worked as the credit-risk team of a US home-loan lender and asked what drives denials and whether the approval rule is fair. I will cover the problem, our questions and the data; Rishabh Kumar will take you through the evidence, and Rishabh Yadav through fairness and the recommendation."

**Slide 2 (problem).** "When someone applies for a mortgage the bank approves or denies. Today it uses fixed rules, for example debt-to-income, DTI, below 43%, plus judgement. If the bank denies good applicants it loses business. If it treats similar people differently by race or area it breaks fair-lending law. So the decision is: which approval rule should the bank follow so that it is safe and fair? Our data is 1.32 million real applications from 2018 to 2023; 13% were denied, about 1 in 8." *We asked: what decision is the lender actually trying to make?*

**Slide 3 (hypotheses as questions).** "We turned the problem into seven questions. Is 43% a cliff (H1)? Do similar applicants get different results by race (H2) or by area (H3)? Do high rates matter (H4)? Can a model predict denial, and do DTI and LTV lead (H5)? Is the model less accurate for some groups (H6)? Do non-banks differ from banks (H7)? The important point: for each one we wrote the decision rule before looking at results, at the 5% level. Supported, not supported and inconclusive are all valid outcomes." Mention the methods if asked: H1 regression discontinuity; H2 and H7 logistic regression and propensity matching; H3 chi-square and logistic regression; H4 correlation; H5 LightGBM with SHAP; H6 fairness metrics.

**Slide 4 (data).** "We used four free public sources. HMDA, from the CFPB, is the base table: one row per application. Census ACS adds the neighbourhood's income, poverty and unemployment, joined on tract and year. FRED adds the mortgage rate and inflation, joined on year. The HMDA Reporter Panel tells us if the lender is a bank or non-bank, joined on lender ID and year. After every join we checked the row count and the match rate: 98.4%, 100% and 99.8%. The result is 1,320,227 rows by 99 columns, which is 13 times the required rows and 5 times the required columns." *We asked: which free public sources can answer these questions?*

**Slide 5 (questions while building the data).** Walk the five rows, one sentence each, with the story: "First, can we use all of HMDA? It is millions of rows a year and the instructor asked us not to use everything, so we took a fixed 5% random sample per state and year. Second, do the sources join? Census tract boundaries changed in 2020, so 2020 and 2021 applications matched only 68%; we mapped them to the 2019 census file and reached 98.4%. Third, does any column give away the answer? Interest rate and fees exist only for approved loans, so a model could just notice the column is empty; we excluded them. Fourth, extreme values: incomes reached 846 million dollars, so we capped them and kept the originals. Fifth, missing values, which are the next slide."

**Slide 6 (missing data).** "We removed 21 duplicates and set 5,785 impossible incomes to missing. Only 48% of rows have an exact DTI; the rest are ranges, so we use the midpoint. The key finding: rows missing DTI, LTV or income are denied 44% of the time, against 9% for complete rows, about five times as often. That means missing is itself a signal. A model can learn 'missing means denied', which makes it look better than it is: AUC is 0.88 on all rows but 0.825 on complete cases. We report 0.825 because it is the honest number, and we re-checked every result with the incomplete rows included." *We asked: can we trust a model that sees missing values?*

## Concepts you must master

- **HMDA:** the Home Mortgage Disclosure Act requires lenders to report every mortgage application; the CFPB publishes it. It has the outcome, loan, income, DTI, race, lender and tract; it does **not** have credit score or repayment.
- **DTI / LTV:** DTI = monthly debt payments / monthly income. LTV = loan / property value.
- **SSOT (single source of truth):** one consistent table, one row per application, with documented join keys, units, duplicate handling and checks. Saved as **Parquet** (compact, column-based, keeps types, about 10x smaller than CSV).
- **Join key and match rate:** the column(s) used to link two tables; match rate is the share of rows that found a partner.
- **Many-to-one validation (`validate="m:1"`):** stops a merge if the right-hand table has duplicate keys, which would silently duplicate rows.
- **Sampling and seed:** a random 5% from each state-year; the seed (42 + year) makes it reproducible.
- **Leakage:** using information the model would not have at decision time (columns only filled for approved loans).
- **Winsorizing:** pulling extremes to the 0.5th/99.5th percentile instead of deleting rows.
- **Complete cases:** rows with DTI, LTV and income all present (1,170,521 rows, 88.7%).
- **Pre-registered decision rules:** the rule that decides supported / not supported is set before seeing results.

## Numbers to know cold

1,320,227 rows, 99 columns; 2018-2023; denial 13.0% (about 1 in 8); 5% sample, seed 42 + year; match rates 98.4% / 100% / 99.8%; 21 duplicates; 5,785 incomes set to missing; winsorized 1.8% of rows; exact DTI 48%; missing vs complete denial 44% vs 9%; AUC 0.88 (all rows) vs 0.825 (complete); required minimum 100,000 rows and 20 variables; incomes up to $846 million; tract match 68% -> 98.4%.

## Code you must know

### Code walkthrough: `01_download.py`
- `parse_years("2018-2023")` turns a range into a list of years.
- `cmd_hmda()`: for each year and state it builds the API URL (`years=...&states=...&loan_purposes=1&actions_taken=1,3`), downloads the CSV, **filters locally** to `lien_status == "1"` and `occupancy_type == "1"`, takes `df.sample(frac=0.05, random_state=42 + year)`, saves a small part file and appends a line to `sampling_log.csv`. It **skips files that already exist**, so an interrupted download resumes.
- `load_env()` reads `CENSUS_KEY` from the git-ignored `.env` file; `cmd_acs()` downloads tract data (6 variables) per state and year, and **rejects any response that is not JSON** (the Census API once returned an HTML "Missing Key" page with status 200, which our first version saved as data).
- `cmd_fred()` downloads the mortgage-rate and CPI series.

### Code walkthrough: `02_build_ssot.py`
- `load_hmda()` reads all part files as **text** (`dtype=str`) so nothing is silently mis-typed.
- `clean_hmda()`: drop duplicates; `NA`/`Exempt` -> NaN; convert numeric columns; **income x 1000**; create `denied`; set impossible values to missing and count them; build `dti_mid`, `dti_is_exact`, `dti_missing`.
- `load_acs()`: builds the 11-digit `census_tract` key (state + county + tract), converts the Census "not available" negatives to NaN, computes poverty and unemployment rates.
- `load_fred()`: yearly mean of the weekly mortgage rate; yearly mean CPI; `cpi_factor_to_2023`.
- `load_panel()`: reads the six Panel files and derives `lender_type` with `np.select`: code 3 -> non-bank mortgage company; codes 1, 2, 5 -> bank affiliate; code 0 and (agency 5 **or** name contains "credit union"/"FCU") -> credit union; code 0 -> bank. (Large credit unions such as Navy Federal are supervised by the CFPB, agency 9, so the name check is needed.)
- `checked_merge()`: left join with `validate="m:1"`, asserts the row count is unchanged, prints the match rate overall and by year.
- `main()`: clean -> map ACS vintage (2020-21 -> ACS 2019) -> join ACS, FRED, Panel -> winsorize -> `*_real` columns, `loan_to_income`, `dti_above_43`, `low_income_tract` -> drop unused detail columns -> save Parquet and the quality report.

### Key ideas to be ready for
SSOT; join keys; many-to-one validation; sampling and seed; tract-vintage problem; winsorizing vs deleting; why read as text; why `income x 1000`; leakage columns; missing-data finding (44% vs 9%).

## Questions on your slides (practise answering out loud)

1. **Why did you take the credit-risk team's point of view?** The lender makes the decision and carries the legal risk, so it is the person who needs an approval rule that is both safe and fair.
2. **Why seven hypotheses, and why written as questions?** Each one tests one thing a lender needs to know. Questions make clear what is being asked; each has a decision rule fixed in advance so we cannot choose the interpretation after seeing results.
3. **Which method tests which hypothesis?** H1 regression discontinuity; H2 logistic regression and propensity matching; H3 chi-square and logistic regression; H4 correlation of yearly rates with denial; H5 LightGBM with SHAP; H6 fairness metrics (error, FPR, FNR gaps); H7 matching like H2.
4. **Did the results match what you expected?** Not all. H1 failed (we expected a jump at 43%), H4 and H5 were inconclusive. We said in the pre-submission that we expected to change some hypotheses.
5. **Why these four sources? Why not Kaggle?** The guidelines ask for public, citable sources. All four are free government data and cover the loan, the neighbourhood, the economy and the lender.
6. **Why sample 5%? Does it bias the results?** The instructor asked us not to use all records. The sample is random within each state-year, so it keeps each state's share; 1.3 million rows is 13 times the minimum and gives narrow confidence intervals. It is less precise for very small groups, so we set a minimum group size of 1,000 for H6.
7. **Why not Apache Spark?** The instructor told us to avoid it unless required. 1.3 million rows fit in pandas and the whole pipeline reruns in 15-20 minutes.
8. **What is a join and how did you check yours?** A join links tables on a key. After each one we assert the row count is unchanged and print the match rate; `validate="m:1"` blocks duplicate keys.
9. **Tell me the tract story.** Joining HMDA 2020 to ACS 2020 matched only 68%. Tracts were redrawn in 2020: HMDA 2018-2021 use 2010 tracts, 2022 onwards use 2020 tracts. We tested which ACS year matched each HMDA year and joined 2020-21 to ACS 2019, which lifted it to about 99%.
10. **What is leakage and which columns did you drop?** Interest rate, rate spread, fees and points exist only for approved loans (100% empty for denied), so a model would predict denial by noticing the column is empty. We also dropped action taken, denial reasons and purchaser type.
11. **Why winsorize instead of delete?** Deleting removes real applicants and biases results; winsorizing keeps the row and limits the influence of absurd values. Originals are kept.
12. **Why is missing data informative?** Denied applications are often closed before the lender collects everything, so missing DTI, LTV or income marks a denial: 44% vs 9%.
13. **Why report complete-case AUC (0.825) instead of 0.88?** The 0.88 is partly the model learning that missing means denied; 0.825 is what the model does when the information is there.
14. **Why not fill in the missing values?** The missingness itself is the signal; filling it in hides that and makes the model look better than it is. We used flags for the all-rows robustness check.
15. **DTI is given in ranges. Is that a problem?** Exact only for 36-49 (48% of rows). We use the midpoint of ranges, which is an approximation, and test robustness on exact rows.
16. **Your pre-submission mentioned a house price index. Where is it?** We used the national 30-year mortgage rate and CPI from FRED; a state-level house price index was not added. It is listed as a limitation; it would help H4.
17. **Does "denied" mean the person would have defaulted?** No. HMDA has no repayment data. We study denial decisions, not default.
18. **What does "13% denied" mean?** 13.0% of the 1.32 million applications in our scope (first-lien, owner-occupied purchase loans that were originated or denied) were denied.

## Your thought-process story (if asked "how did you approach the data?")

"We started from the question, not the data: what would a lender need to know? That told us which fields we need. Then each problem we hit became a question: too many rows, so we sampled; sources not matching, so we investigated and found the 2020 tract change; columns that give the answer away, so we excluded them; missing values that turned out to carry information, so we judged the model on complete cases and re-checked everything with the incomplete rows included."

## Part 3. Quick answers for questions on other people's slides

- **What is the project in one sentence?** We built one dataset from four public sources, tested seven pre-set hypotheses about what drives mortgage denial and whether there are unfair gaps, built an explainable model, audited it for fairness and wrote a scoring API and dashboard.
- **Headline results?** No cliff at 43% DTI (denial rises gradually, jumps from 50%); gaps persist after comparing similar applicants (race 4.7 pts, odds ratio 1.73); model AUC 0.825 on unseen 2023 vs 0.68 for the DTI rule; it is a triage tool because HMDA has no credit score.
- **Scorecard?** Supported: H2, H3, H6, H7. Not supported: H1. Inconclusive: H4, H5.
- **Biggest limitation?** No credit score (recall only 45%) and findings are associations.
- **Which hypothesis could you not test?** H8: does credit score explain the race gap? Public HMDA has only the score type, not the score.
- **Did you use AI?** Yes, with the instructor's approval; it is disclosed in the README and report, and each of us can explain our parts.
