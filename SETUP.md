# Run the project

Use `pipe.ipynb` in Snowflake for ingestion, then run dbt from local PowerShell. Run local commands from the repository folder. SQL blocks belong in a Snowflake SQL worksheet.

## 1. Create the Snowflake objects

In your Enterprise trial, run [bootstrap.sql](bootstrap.sql) as ACCOUNTADMIN. It creates `HOMEWORK`, the `RAW`, `STAGING` and `MARTS` schemas, `HOMEWORK_WH` and `HOMEWORK_ENGINEER`, and assigns the role to your current user.

For notebook creation and access to the configured CSV host, run this once as ACCOUNTADMIN:

```sql
USE ROLE ACCOUNTADMIN;
GRANT CREATE NOTEBOOK ON SCHEMA HOMEWORK.RAW TO ROLE HOMEWORK_ENGINEER;

CREATE OR REPLACE NETWORK RULE HOMEWORK.RAW.HOMEWORK_CSV_HOSTS
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = ('gist.githubusercontent.com:443');
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION HOMEWORK_CSV_ACCESS
    ALLOWED_NETWORK_RULES = (HOMEWORK.RAW.HOMEWORK_CSV_HOSTS)
    ENABLED = TRUE;
GRANT USAGE ON INTEGRATION HOMEWORK_CSV_ACCESS TO ROLE HOMEWORK_ENGINEER;
```

Skip this setup when the objects and integration are already configured. If you change the source host, update the network rule, including any required redirect hosts.

## 2. Load with the notebook

1. Switch to `HOMEWORK_ENGINEER` and import [pipe.ipynb](pipe.ipynb) into `HOMEWORK.RAW`, or open the existing notebook.
2. Use `HOMEWORK_WH` as the query warehouse and notebook warehouse where applicable. Ensure `snowflake-snowpark-python` is available in the runtime.
3. Enable `HOMEWORK_CSV_ACCESS` in the notebook's external-access settings or runtime configuration, then restart the session.
4. Check the direct HTTPS URL in the Setup cell and run all cells in order. No manual CSV upload or local key is needed for this step.
5. Expect 1,000 source and loaded rows for the supplied snapshot. Keep the source hash and COPY/publish query IDs from the report. Stop the notebook session when finished.

If the download fails with `Name or service not known`, check that `CSV` points to `gist.githubusercontent.com`, that the integration above is enabled on this notebook/runtime, and that you restarted the session. Granting usage alone does not attach an integration to a notebook.

The notebook writes `HOMEWORK.RAW.HOMEWORK_OBT` with eight text columns. Run [profiling.sql](profiling.sql) to inspect the loaded source. Existing raw tables must use the same column order and unquoted or uppercase identifiers.

## 3. Prepare local dbt

On a fresh clone, install Python 3.12, then run in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Reuse your existing environment if already configured. The project requires dbt 1.11; the dependency files pin the tested versions.

If you do not already have a registered key, generate one and export its registration SQL:

```powershell
.\.venv\Scripts\python.exe tools/create_key.py
.\.venv\Scripts\python.exe tools/export_public_key.py --user YOUR_SNOWFLAKE_LOGIN
```

Run the generated `.secrets/register_public_key.sql` in Snowflake as ACCOUNTADMIN. Keep the encrypted private key and passphrase local. The creation script refuses to overwrite an existing key.

Set the connection variables in the same PowerShell session:

```powershell
$env:SNOWFLAKE_ACCOUNT = 'YOUR_ORGANIZATION-YOUR_ACCOUNT'
$env:SNOWFLAKE_USER = 'YOUR_SNOWFLAKE_LOGIN'
$env:SNOWFLAKE_PRIVATE_KEY_PATH = (Resolve-Path '.secrets/snowflake_key.p8').Path
$keySecret = Read-Host 'Private-key passphrase' -AsSecureString
$keyCredential = [System.Management.Automation.PSCredential]::new('key', $keySecret)
$env:DBT_ENV_SECRET_PRIVATE_KEY_PASSPHRASE = $keyCredential.GetNetworkCredential().Password
$env:DBT_SEND_ANONYMOUS_USAGE_STATS = 'false'

.\.venv\Scripts\dbt.exe debug --project-dir dbt --profiles-dir dbt
```

Use the organization-account identifier, not the browser URL. Re-set these variables in a new terminal. Notebook ingestion and local dbt use separate sessions.

## 4. Build and verify

After loading RAW, run locally:

```powershell
.\.venv\Scripts\dbt.exe build --project-dir dbt --profiles-dir dbt
```

dbt creates three staging views, four mart tables and the weekly aggregation view, and runs the data and unit tests. Do not upload individual dbt SQL files into Snowflake or run `dbt init` again.

Run [verify.sql](verify.sql) in Snowflake. Expect 1,000 customers and orders, 3 products, 1,674 items, 144 weeks and 424 week/product rows. Compare with [evidence/local_profile.json](evidence/local_profile.json). Repeat the load and build to check that business results stay unchanged.

To generate and browse model documentation:

```powershell
.\.venv\Scripts\dbt.exe docs generate --project-dir dbt --profiles-dir dbt
.\.venv\Scripts\dbt.exe docs serve --project-dir dbt --profiles-dir dbt --port 8080
```

Stop the documentation server with Ctrl+C. If a build fails, inspect its first failing model/test and `dbt/logs/dbt.log` before rerunning.

## 5. Give the reviewer access

After the final build, run [reviewer_access.sql](reviewer_access.sql) as ACCOUNTADMIN. Create the reviewer user separately in a private worksheet:

```sql
USE ROLE ACCOUNTADMIN;
CREATE USER HOMEWORK_REVIEWER
    TYPE = PERSON
    PASSWORD = 'REPLACE_WITH_UNIQUE_TEMPORARY_PASSWORD'
    DEFAULT_ROLE = HOMEWORK_REVIEWER_ROLE
    DEFAULT_WAREHOUSE = REVIEWER_WH
    MUST_CHANGE_PASSWORD = TRUE;
GRANT ROLE HOMEWORK_REVIEWER_ROLE TO USER HOMEWORK_REVIEWER;
```

Do not save the populated password statement in Git. The reviewer completes the password change and any required MFA on their first sign-in.

To check the role with your own user, temporarily grant it to yourself:

```sql
USE ROLE ACCOUNTADMIN;
SET setup_user = CURRENT_USER();
GRANT ROLE HOMEWORK_REVIEWER_ROLE TO USER IDENTIFIER($setup_user);
USE ROLE HOMEWORK_REVIEWER_ROLE;
USE SECONDARY ROLES NONE;
USE WAREHOUSE REVIEWER_WH;
SELECT * FROM HOMEWORK.MARTS.AGG_WEEKLY_PRODUCT LIMIT 10;
SELECT COUNT(*) FROM HOMEWORK.MARTS.FCT_ORDER_ITEMS;
```

Both SELECTs should succeed. Run these separately; both must be denied:

```sql
SELECT * FROM HOMEWORK.RAW.HOMEWORK_OBT LIMIT 1;
DELETE FROM HOMEWORK.MARTS.FCT_ORDERS WHERE FALSE;
```

Remove the temporary role assignment afterwards:

```sql
USE ROLE ACCOUNTADMIN;
SET setup_user = CURRENT_USER();
REVOKE ROLE HOMEWORK_REVIEWER_ROLE FROM USER IDENTIFIER($setup_user);
```

Send the GitHub repository link and share the Snowflake account URL, reviewer username and temporary password privately. Verify the reviewer can sign in separately from testing role permissions.

## Optional local loader

The original `loader.py` is retained. Skip it when using the notebook. It uses the same local credentials and publishes the same raw table:

```powershell
$env:HOMEWORK_CSV_URL = 'YOUR_DIRECT_HTTPS_CSV_URL'
.\.venv\Scripts\python.exe loader.py
```

For offline checks:

```powershell
.\.venv\Scripts\python.exe loader.py --file homework.csv --validate-only
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tools/profile_csv.py --output evidence/local_profile.json
```
