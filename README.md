# Fair Mortgage Approval Decisions

Advanced Data Science (ADS) end-term project, Group 8.
**Stakeholder:** the credit-risk team of a US home-loan lender.
**Question:** what drives mortgage denials, are there unfair gaps between groups, and can we build a fair, explainable approval model?
Framework: BADIR (Business question, Analysis plan, Data, Insights, Recommendation).

## Data (all public, no Kaggle)
| Source | What | Link |
|---|---|---|
| HMDA (CFPB/FFIEC) | mortgage applications 2018-2023 | https://ffiec.cfpb.gov/data-browser/ |
| HMDA Reporter Panel (CFPB/FFIEC) | lender type (bank / credit union / non-bank) | https://ffiec.cfpb.gov/data-publication/ |
| Census ACS 5-year | tract income, house value, poverty, unemployment | https://api.census.gov/ |
| FRED | 30-year mortgage rate, CPI (inflation) | https://fred.stlouisfed.org/ |

**Sample:** first-lien, owner-occupied home-purchase applications that were originated or denied; a fixed 5% random sample per state-year (seed 42 + year), about 1.3 million rows. Every download is logged in `data/raw/hmda/sampling_log.csv`.
**Single source of truth:** `data/processed/ssot.parquet` (built by `src/02_build_ssot.py`; joins, match rates and quality checks are written to `reports/data_quality_report.md`).

## Reproduce
1. `pip install -r requirements.txt`
2. Get a free Census API key (https://api.census.gov/data/key_signup.html) and put `CENSUS_KEY=...` in a file named `.env` (git-ignored).
3. Download the data:
   ```
   python src/01_download.py hmda --years 2018-2023 --states all     # slow: ~300 state-year requests
   python src/01_download.py acs  --years 2018-2023
   python src/01_download.py fred
   ```
4. **Manual step:** download the HMDA *Reporter Panel* CSV zip for 2018-2023 from the data-publication site above and unzip each year into `data/raw/panel/<year>/`.
5. `python src/02_build_ssot.py` builds the SSOT table.
6. Run the notebooks in order:
   - `notebooks/01_eda.ipynb` - data audit and exploratory analysis
   - `notebooks/02_hypothesis_tests.ipynb` - H1-H4 and H7 (RDD, chi-square, logistic regression, propensity score matching)
   - `notebooks/03_model_fairness.ipynb` - H5 and H6 (gradient boosting, SHAP, calibration, fairness audit, reweighing); saves `models/`
7. Scoring API and dashboard: `uvicorn src.api:app`, then open http://127.0.0.1:8000/ for the dashboard (type an application, see approve or deny) or http://127.0.0.1:8000/docs for the raw API. Tests: `python tests/test_api.py`.

Raw and processed data are not committed (size); the scripts rebuild them. Results table: `reports/hypothesis_results.csv`. Figures: `reports/figures/`.

## Method scope
Only methods from the ADS course handout. Apache Spark is not used (instructor advised avoiding it unless required).

## AI assistance
Parts of the code were written with AI assistance (Claude Code), approved by the course instructor. The team reviews it and must be able to explain all of it.
