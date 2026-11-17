# Banking Transaction Data Quality & Reconciliation

A reproducible analytics portfolio project by **Akshitha Thakur**, aligned with banking reporting, Python/SQL automation, data validation, reconciliation, and root-cause investigation.

## Business problem
A reporting team receives transaction extracts from an operational system and a downstream ledger. Bad source records and mismatched reporting populations can distort KPIs. This project quarantines invalid records, reconciles accepted transactions against a ledger, and produces reviewable exception evidence.

**All data is synthetic. No employer, customer, or production banking data is included.** This is a portfolio demonstration, not a production banking control or fraud model.

## Run
Requires Python 3.10 or newer; no third-party packages, credentials, or cloud services.
```bash
python -m unittest -v
python pipeline.py
```
Open `reports/dashboard.html` in your browser. CSV outputs can be imported into Excel or Power BI.
Alternatively open the **Actions** tab, select a successful validation run, and download the `banking-quality-reports` artifact.

## What is implemented
- Deterministic generation of 1,000 base transactions across 90 days and three channels.
- Source validation: duplicate/missing IDs, missing accounts, invalid dates, unknown channels, and nonpositive amounts.
- Quarantine of **all** occurrences of a duplicate identifier; no arbitrary survivor.
- SQLite joins and two-sided reconciliation: source-only, ledger-only, and amount mismatches.
- Integer cents for exact monetary controls; missing values remain distinct from zero.
- CSV exception evidence, channel KPIs, JSON control metrics, and a standalone HTML dashboard.
- Unit tests and GitHub Actions for reproducibility.

## Seeded control expectations
These are expected outcomes of the designed fixture, not real-world performance claims.

| Control | Expected |
|---|---:|
| Raw source rows | 1,001 |
| Accepted rows | 995 |
| Quarantined rows | 6 |
| Row acceptance | 99.40% |
| Ledger rows | 1,000 |
| Reconciliation exceptions | 8 |

Acceptance is the share of rows passing implemented rules, **not** measured reporting accuracy. A source quarantine can also create a ledger-only exception; the two counts must not be added as distinct bad transactions.

## Root-cause walkthrough
| Seeded issue | Impact | Investigation / action |
|---|---|---|
| T0001 duplicated | Both occurrences quarantined | Inspect upstream retry/idempotency behavior |
| T0010 missing account | Referential completeness failure | Repair account mapping at source |
| T0020 negative amount | Amount validation failure | Confirm transaction type/sign convention |
| T0030 invalid date | Calendar validation failure | Correct parsing or source value |
| T0040 unknown channel | Domain validation failure | Review reference data |
| T0050 missing from ledger | Source-only break | Inspect downstream ingestion |
| One ledger amount changed by 500 cents | Amount mismatch | Trace transformation or adjustment |
| EXTRA ledger record | Ledger-only break | Inspect lineage and source coverage |

The demo assumes positive transaction amounts, a single USD currency, and unique ledger keys. Production use would need ledger validation, signed debit/credit semantics, currency partitions, freshness checks, access controls, and business-approved tolerances.

## Files
- `pipeline.py`: generation, validation, SQLite reconciliation, exports, dashboard.
- `test_pipeline.py`: duplicate, date/amount, population, join, and end-to-end tests.
- `sql/controls.sql`: reusable population, duplicate, monthly KPI, and amount controls.
- `.github/workflows/validate.yml`: tests and downloadable generated reports.

## Skills demonstrated
Python · SQL · SQLite · ETL · data quality · reconciliation · KPI monitoring · analytical documentation · automated testing.

This implementation runs locally; it does not claim to deploy Azure, Databricks, PySpark, or Power BI.
