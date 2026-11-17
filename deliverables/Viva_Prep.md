# Viva Preparation: Fair Mortgage Approval Decisions (Group 8)

**Course:** Advanced Data Science (CSE3105), BML Munjal University
**Team:** Rishabh Kumar (240605), Rishabh Yadav (240606), Kanishk Chahar (240953), Pari Garg
**Repository:** https://github.com/Rishhhhub/fair-mortgage-approval

> **Why this document exists.** The course handout says evaluation includes questions on the work, and that AI-assisted code is allowed only if the team is thorough with it. Every member must be able to explain **the whole project (Part A)** and **their own part in depth (Part B)**. Read Part A first, then your own section in Part B, then the question lists.
>
> **Before the viva:** each person fills in the owner line of their section in Part B (marked `Owner: ______`). The split below is by project component; the team decides who owns which.

---

# PART A. The whole project

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

---

## A11. Demo script (2 minutes)

1. Open a terminal in the project folder: `uvicorn src.api:app`
2. Open http://127.0.0.1:8000/docs, expand **POST /score**, click "Try it out".
3. Low-risk example: `{"dti_mid": 30, "loan_to_value_ratio": 75, "income_w": 150000, "loan_amount_w": 300000, "property_value_w": 400000}` -> probability about 0.20, "LOW DENIAL RISK".
4. High-risk example: `{"dti_mid": 62, "loan_to_value_ratio": 100, "income_w": 40000, "loan_amount_w": 300000, "property_value_w": 300000}` -> about 0.98, "REFER FOR MANUAL REVIEW", with the top 3 factors.
5. Show that adding `"race": "x"` returns an error. That is the fair-lending guarantee.

---

# PART B. Individual parts

> Split by project component. **Fill in the owner of each part.** Even if you did not build a part, read its "Key ideas" so you can answer basic questions about it.

---

## B1. Data acquisition and the single source of truth

**Owner: ______________________**

**Files:** `src/01_download.py`, `src/02_build_ssot.py`, `reports/data_quality_report.md`, `data/raw/hmda/sampling_log.csv`.

### What this part covers
Downloading the four sources, sampling HMDA, cleaning and joining everything into `ssot.parquet`, with documented checks.

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

### Questions for this part
1. **Why one state at a time?** The API needs a geography and allows two filters; per-state downloads are small, resumable and let us sample proportionally.
2. **Why `dtype=str`?** To avoid wrong type guesses; we convert explicitly and turn failures into missing values.
3. **What does `validate="m:1"` do?** It stops the merge if the right-hand table has duplicate keys, which would silently duplicate rows.
4. **How did you find the tract problem?** The 2020 match rate was 68%. We compared HMDA tracts against each ACS year's tracts and saw 2018-2020 HMDA matched ACS 2018/2019 at 100%.
5. **Why winsorize and not delete outliers?** Deleting would drop real applicants and bias results; winsorizing keeps rows and limits extreme influence. Originals are kept.
6. **How is `dti_mid` built and why is it a limitation?** Exact when given, else the midpoint of the range; midpoints are an approximation, so we test robustness on exact rows only.
7. **How do you know a join did not drop or duplicate rows?** `checked_merge` asserts equal row counts before and after.
8. **How is lender type decided?** From the Reporter Panel `other_lender_code` plus agency code and name for credit unions (see above).
9. **What does the quality report contain?** Rows loaded, duplicates, impossible values, join match rates by year, winsorizing limits, missing-value shares, final shape.
10. **What would break reproducibility?** Missing `.env` Census key, missing Panel files (manual download), or API changes.

---

## B2. Exploration and hypothesis testing (H1, H2, H3, H4, H7)

**Owner: ______________________**

**Files:** `notebooks/01_eda.ipynb`, `notebooks/02_hypothesis_tests.ipynb`, `reports/hypothesis_results.csv`.

### What this part covers
The data audit and EDA, and the statistical tests: RDD (H1), chi-square, logistic regression and propensity matching (H2, H3, H7), and the yearly correlation (H4), plus the missing-data robustness checks.

### Code walkthrough: `01_eda.ipynb`
Sections: data audit (rows per year, missing values), outcome by year, denial reasons, DTI chart, race, neighbourhood income, LTV, income/loan distributions, correlations, **leakage check**, lender concentration. Each chart ends with a title that states the takeaway; EDA is descriptive only.

### Code walkthrough: `02_hypothesis_tests.ipynb`
- **Setup:** `record()` stores each hypothesis' verdict; `ALPHA = 0.05`.
- **`rdd(data, cutoff, bw)`** (H1): keeps DTI within `bw` points each side, builds `above` and `x = dti - (cutoff + 0.5)`, fits `denied ~ above + x + above:x` by OLS with **state-clustered** standard errors, and returns the jump in percentage points with its CI. Run for bandwidths 2/3/5/7, for **placebo cutoffs 38-46**, and by loan type. Verdict rule: positive, significant and larger than every placebo.
- **Preparing H2/H3/H4:** complete cases (1,170,521 rows); a 400,000-row random sample for regressions (seed 42).
- **`fit_logit(formula, data)`**: logistic regression with state-clustered standard errors. **`odds_ratio(model, var)`**: exponentiates the coefficient and CI. **`adj_gap(model, data, var)`**: predicts for everyone with the variable set to 1 and to 0 and averages the difference (percentage points).
- **H2 PSM:** one-hot encode categorical variables, standardise numerics, fit a logistic **propensity model** (`LogisticRegression`), take the logit of the score, find each Black applicant's **nearest White neighbour** (`NearestNeighbors`, 1-D), keep matches within a **caliper of 0.2 sd**, compute the ATT and a **bootstrap CI** (500 resamples of matched pairs). A balance plot shows standardised mean differences before and after.
- **H3:** low/moderate tract = tract income below 80% of metro income; chi-square, then logit with state fixed effects.
- **H4:** logistic model with year effects -> adjusted yearly denial rate (predict with the year set to each value) -> Pearson correlation with the yearly mortgage rate (6 points).
- **H7:** non-bank vs bank, same two-step design as H2.
- **Robustness:** repeat H2 and H3 on all rows with median-filled values plus missing flags.

### Key ideas to be ready for
RDD logic and placebo tests; why clustered SEs; OR vs adjusted gap; propensity score, caliper, ATT, balance; matching with replacement; why complete cases and the robustness check; association vs causation; pre-set decision rules.

### Questions for this part
1. **Explain RDD to a non-statistician.** People with DTI 43 and 44 are almost the same; if the 43% rule bites, denial should jump between them beyond the normal trend. We found no such jump.
2. **Why placebo cutoffs?** To see whether 43 stands out. Fake cutoffs at 44 and 45 show larger positive jumps, so 43 is not special.
3. **Why do the RDD results change with the bandwidth?** The jump is small and the trend is steady; a wider window is dominated by the slope. That sensitivity is part of why we say "no break".
4. **Why cluster by state?** Applications in the same state are not independent (lenders, rules), so ordinary SEs would be too small.
5. **What is an odds ratio of 1.73?** 73% higher odds of denial, after controlling for the listed variables. The adjusted gap is about 4.6 pp.
6. **What does matching add over regression?** It compares like with like without assuming a linear relationship, and we can check balance. Both agree here (OR 1.73 and gap 4.71 pp).
7. **How do you know matching worked?** Standardised mean differences fall below 0.1 on DTI, LTV, income, loan amount and tract income.
8. **Matching with replacement: any issue?** Control applications can be reused, so the bootstrap standard error is approximate. We say so.
9. **Why only 400k rows for the regressions?** Speed. The matching and the descriptive results use all complete rows; results are stable.
10. **H3 is "supported" but small. How do you explain that?** Raw gap 3.6 pp shrinks to 1.2 pp once applicants are comparable; neighbourhood matters a little beyond the applicant's own finances.
11. **H7: non-banks deny less. Does that mean they are looser?** Not necessarily. They may screen before a formal application and specialise in FHA/VA loans; no credit score is available.
12. **Why are all hypotheses judged by rules fixed in advance?** To avoid choosing the interpretation after seeing the result.

---

## B3. Model, explainability and fairness (H5, H6)

**Owner: ______________________**

**Files:** `notebooks/03_model_fairness.ipynb`, `models/lgbm_denial.txt`, `models/model_card.json`.

### What this part covers
Feature choice, baselines, LightGBM tuning and evaluation, calibration, SHAP, the fairness audit, reweighing and the threshold table.

### Code walkthrough: `03_model_fairness.ipynb`
- **Features:** `NUMERIC` (12) + `CATEG` (5) = 17. `AUDIT = [derived_race, derived_sex]` are only for auditing. Categoricals use the pandas `category` type; missing categories become "missing". `complete` marks rows with DTI, LTV and income.
- **Split:** `train` 2018-2021, `valid` 2022, `fit_all` 2018-2022, `test` 2023.
- **Baselines:** the DTI rule of thumb (DTI used directly as the score) and a logistic regression with median filling and missing flags.
- **Tuning:** 6 random draws of `num_leaves`, `min_child_samples`, `feature_fraction`, `lambda_l2`; train on 2018-2021 with **early stopping** on 2022 AUC; the best setting is refit on 2018-2022 with 1.1x the best number of trees (305).
- **Threshold:** the grid 0.05-0.60; pick the F1 maximum on the 2022 predictions (0.31).
- **Evaluation:** AUC, PR-AUC, Brier, precision, recall, accuracy on all test rows, complete cases and rows with missing values; bootstrap CI (100 resamples) for the complete-case AUC; ROC curves vs baselines.
- **Calibration:** `IsotonicRegression` fitted on 2022; reliability curve.
- **SHAP:** `final.predict(X, pred_contrib=True)` on 50,000 complete test rows; mean |SHAP| per feature; DTI dependence curve; grouped importance; **sensitivity without `preapproval`** (retrain, AUC 0.814).
- **Fairness:** `fairness_table()` computes per-group n, actual and predicted denial rate, error rate, FPR, FNR and the gap vs White with a normal-approximation 95% CI (`diff_ci`). H6 flags any gap above 5 pp with CI above 0 for groups with n >= 1,000. Also the 80% approval-ratio rule and a **threshold sweep** (0.20-0.50).
- **Mitigation:** Kamiran-Calders **reweighing** weights, retrain, recompute gaps.
- **Saving:** `lgbm_denial.txt` (the model) and `model_card.json` (features, categories, threshold, AUC, medians, exclusions); also updates `hypothesis_results.csv` for H5/H6.

### Key ideas to be ready for
Time-based split; why complete-case AUC; leakage; threshold choice; AUC vs precision/recall; SHAP; calibration; FPR/FNR; the 80% rule; reweighing; why gaps barely changed.

### Questions for this part
1. **Why LightGBM?** Strong on tabular data, handles missing values and categories natively, fast on 1M rows, and gives exact TreeSHAP values.
2. **Why compare with a DTI rule and logistic regression?** The DTI rule is the lender's current practice; logistic regression is the simple explainable benchmark. LightGBM beats both (0.825 vs 0.682 and 0.770 on complete cases).
3. **What does AUC 0.825 mean?** A random denied application scores higher than a random approved one 82.5% of the time (complete cases, unseen year).
4. **Why is recall only 45%?** With no credit score the model cannot see credit history (28% of denials) and other reasons; the threshold also trades recall for precision.
5. **Why did you pick 0.31?** Maximum F1 on 2022 validation; the threshold table in the report shows trade-offs (for example 0.15 flags 10.7% of applications with 52% precision).
6. **What does `pred_contrib=True` give?** SHAP values (log-odds contributions) per feature per row, plus a baseline in the last column.
7. **What does the `preapproval` result mean?** It marks pre-approval requests, which have a different decision process. It is an application type, so we also report the model without it (AUC 0.814, DTI becomes the top driver).
8. **How do you read a false-negative rate of 50% for Asian applicants?** Half of the Asian applicants the lender denied would have been approved by the model, versus 35.5% for White applicants. It is the one significant gap; it is stable across thresholds.
9. **Why did reweighing not help?** Race is not a model input, so the model had little group dependence to remove; gaps were already small.
10. **What does the 80% rule say here?** The model's approval rate for Black applicants is 0.89 of White applicants', above 0.80.
11. **Is the model calibrated?** Reasonably: the isotonic recalibration did not change the Brier score (0.0675).
12. **Why did you exclude the tract minority share?** It is nearly a proxy for race; including it would reintroduce race indirectly.
13. **What is the difference between ROC-AUC and PR-AUC here?** With 13-15% positives, PR-AUC (0.587 on complete cases) is a harsher view of precision/recall than ROC-AUC (0.825).

---

## B4. Scoring API, recommendations, presentation and report

**Owner: ______________________**

**Files:** `src/api.py`, `tests/test_api.py`, `deliverables/` (report and slides), `README.md`.

### What this part covers
The BADIR "Recommendation": the scoring API, the policy recommendations and roadmap, the slides and the written report, and reproducibility on GitHub.

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

### Deliverables and submission
- **Slides** (`Group_8_..._Presentation.pptx/pdf`): 17 slides plus 3 appendix slides, following the teacher's three stages; speaker notes on every slide.
- **Report** (`Group_8_..._Report.docx/pdf`): follows the teacher's template (9 chapters). **Before submitting:** fill the contribution matrix (Chapter 8), add Pari Garg's enrollment number, sign the declaration, and add the **plagiarism report page** after the last page.
- **Google Form needs:** presentation PDF, report PDF (with one plagiarism page at the end), full plagiarism report PDF, data used (the Parquet file is 97 MB), source link (the GitHub URL), and the code zipped.

### Key ideas to be ready for
What the API does and does not accept; why it recommends review and does not deny; how the recommendations follow from the findings; the roadmap and indicators; what the report and slides contain.

### Questions for this part
1. **What does the API return?** Probability of denial, a recommendation, the top 3 SHAP factors, and a decision-support note.
2. **How does the API protect against using race?** The model has no race input, and the API schema rejects any field not in its list with an error (tested).
3. **Why "refer for manual review" and not "deny"?** The model lacks a credit score and learns past decisions; a human must make the final call.
4. **How does the API make sure inputs match training?** It uses the saved model card's feature list and category lists, and computes `loan_to_income` the same way.
5. **How do your recommendations follow from the findings?** No cliff at 43% -> graduated scoring; model beats the rule but has limits -> triage; persistent gaps -> monitoring; no credit score -> pilot on lender data.
6. **What are your success indicators?** AUC on the lender's data, review hours per file, false-positive rate, group gaps under 5 pp, drift alerts.
7. **What are the limits of the roadmap?** Timelines are proposals for discussion with the stakeholder.
8. **What is in the repository and how do I run it?** README lists steps; code, notebooks, figures, saved model and tests are public; raw data is not committed because of size (scripts rebuild it).
9. **How is the report structured?** The teacher's template: introduction, problem statement, dataset, literature review, methodology, technology stack, results, team contribution, conclusions, references, appendices.
10. **What references did you use?** Public data sources plus Munnell et al. (1996), Bartlett et al. (2022), Fuster et al. (2022) on mortgage data; Imbens & Lemieux (2008), Rosenbaum & Rubin (1983), Ke et al. (2017), Lundberg & Lee (2017), Hardt et al. (2016) and Kamiran & Calders (2012) on methods.

---

## Last-minute checklist

- [ ] Each person can give the one-minute summary (A1).
- [ ] Each person can name the seven hypotheses and their verdicts (A5).
- [ ] Each person can state three limitations (A7).
- [ ] Each person has read their part in Part B and can walk through its code.
- [ ] Each person can name the hypothesis we could not test and why (A10, H8).
- [ ] The demo works (A11): run it once before the viva.
- [ ] Owner lines in Part B and the contribution matrix in the report are filled in, consistent with each other.
