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

Earlier loading and dbt runs were reported successful during setup; their query IDs and build logs are not archived here. After removing the notebook's workspace-file override, the Snowflake URL download encountered a hostname-resolution error. Integration creation then confirmed that external access is not supported on this trial account. The URL works locally. Use the existing local loader as described in [SETUP.md](../SETUP.md), then run `dbt build` and `verify.sql`. A successful URL load inside the Snowflake notebook is not claimed.

Expected unchanged-snapshot results: 1,000 orders and customers, 3 products, 1,674 items, 144 weeks and 424 week/product rows. Winning weeks are A1 = 1, B1 = 139 and C1 = 4. For week 2024-05-27, A1 wins with revenue 500.
