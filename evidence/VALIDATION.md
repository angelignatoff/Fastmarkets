# Validation

## Recorded local checks

- Python 3.12, dbt-core 1.11.15 and dbt-snowflake 1.11.6; dependencies recorded in `requirements-lock.txt`.
- Original Python loader: 11 tests passed, using mocked downloads and Snowflake connections for failure cases.
- Supplied CSV: 1,000 records, 1,674 items and zero exact header/line-total mismatches.
- Independent reference: [local_profile.json](local_profile.json), calculated with Python Decimal.
- dbt parse: eight models, 65 data-test definitions and one unit test covering ties and calendar boundaries. Parsing does not establish a live test pass.
- Submission cleanup: notebook syntax, single source configuration, local CSV validation and mocked publication/failure cleanup checks passed. The original loader's 11 tests passed again.
- Live HTTPS download checked locally: 1,000 records, identical parsed values to `homework.csv`. Download SHA-256: `85178e0f71545320eeb2b1e145af06806c83e98d0a24c9e881fd4909d467ef31`. The file bytes differ from the local reference, but the parsed CSV records match.

## Snowflake execution

The supplied execution output confirms a successful HTTPS load through the local `loader.py`, followed by a successful live `dbt build`:

| Check | Actual result |
| --- | --- |
| Source / loaded rows | 1,000 / 1,000 |
| Source SHA-256 | `85178e0f71545320eeb2b1e145af06806c83e98d0a24c9e881fd4909d467ef31` |
| COPY query ID | `01c73309-0000-9d25-0001-23820009320e` |
| Publication query ID | `01c73309-0000-9d25-0001-238200093212` |
| Models built | 4 tables and 4 views |
| Tests passed | 65 data tests and 1 unit test |
| dbt summary | `PASS=74 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=74` |
| Table row counts | 1,000 orders, 1,000 customers, 3 products, 1,674 items |

The Snowflake notebook URL route remains blocked by this trial account's external-access restriction. The confirmed submission route is local URL extraction/loading followed by dbt. Final `verify.sql` inspection and reviewer-access checks are described in [SETUP.md](../SETUP.md); this build output does not establish those separate checks.

Expected unchanged-snapshot results: 1,000 orders and customers, 3 products, 1,674 items, 144 weeks and 424 week/product rows. Winning weeks are A1 = 1, B1 = 139 and C1 = 4. For week 2024-05-27, A1 wins with revenue 500.
