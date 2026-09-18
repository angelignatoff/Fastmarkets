# Validation record

## Completed locally

Environment: Windows, Python 3.12, dbt-core 1.11.15, dbt-snowflake 1.11.6.
Resolved dependency versions are recorded in requirements-lock.txt.

| Check | Result |
| --- | --- |
| Python loader tests | 11 passed |
| Dependency consistency (pip check) | No broken requirements |
| Local CSV validation | 1,000 records accepted |
| Independent reference calculation | Saved in local_profile.json |
| dbt parse, with placeholder connection settings | Passed |
| Parsed models | Eight: three staging views, four mart tables, one aggregate view |
| Parsed dbt data tests | 65 definitions |
| Parsed dbt unit tests | One definition covering ties and calendar boundaries |

These checks did not connect to Snowflake. Parsed tests have not yet executed.
The loader failure tests mock the Snowflake connector. The HTTPS test mocks the
download response; it does not retrieve the original assignment URL.

Reproduce from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe loader.py --file homework.csv --validate-only
.\.venv\Scripts\python.exe tools/profile_csv.py --output evidence/local_profile.json
```

After setting the environment variables described in SETUP.md:

```powershell
.\.venv\Scripts\dbt.exe parse --project-dir dbt --profiles-dir dbt --no-partial-parse
```

## Required live checks

Fill these in only after actually running them. Include the date and relevant
query IDs or a brief result. Keep credentials and unredacted private logs out of Git.

| Check | Status / actual result |
| --- | --- |
| Enterprise trial and bootstrap.sql | Pending |
| Key registration and dbt debug | Pending |
| Local-file load: count, source hash, COPY/publish query IDs | Pending |
| Original-URL download and load | Pending original URL |
| profiling.sql in Snowflake | Pending |
| dbt build: models, data tests and unit test | Pending |
| verify.sql matches local_profile.json | Pending |
| Second load/build gives the same business results | Pending |
| dbt docs generate | Pending |
| Reviewer role can query all submitted objects | Pending |
| Reviewer role cannot read RAW or write MARTS | Pending |
| Reviewer user can complete sign-in/MFA | Pending |
| GitHub repository published/shared | Pending |

The project is ready for a first live run; this record is not evidence of a
successful Snowflake deployment.
