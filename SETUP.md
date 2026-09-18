# Run the project, step by step

The code is already written. Your next job is to create the trial, configure authentication, run the loader and dbt, and verify the results.

**Local PowerShell:** run Python and dbt commands from this project folder.
**Snowflake browser:** paste the SQL files into a SQL worksheet or SQL file in a Workspace, then run them.
Do not upload the dbt SQL files individually into Snowflake. dbt reads them locally and creates the tables/views remotely.

## 1. Create and sign into Snowflake

Create your Enterprise trial at https://signup.snowflake.com/ if you have not already. Complete the browser sign-in and MFA setup.

Open a SQL worksheet/editor in Snowsight (usually under Workspaces, or Worksheets in the older interface). Select ACCOUNTADMIN for initial setup.

Save your account URL. Find your account identifier in the account details/configuration panel. Python/dbt need the organization-account identifier, not an https URL or the entire app.snowflake.com address.

## 2. Create the Snowflake objects

Open bootstrap.sql locally, paste its complete contents into the Snowflake SQL editor, and run all statements in order.

It creates:
- HOMEWORK database, with RAW, STAGING and MARTS schemas.
- HOMEWORK_WH, an XSMALL warehouse.
- HOMEWORK_ENGINEER, assigned to the user currently running the script.

Use ACCOUNTADMIN only for this setup and access management. Python and dbt explicitly use HOMEWORK_ENGINEER.

Do not run the original, superseded loader against the same raw table. This version expects eight VARCHAR columns. If you already built the old typed/VARIANT raw table, preserve it under a different name and let this loader create a fresh HOMEWORK_OBT. Existing objects owned by another role also need an explicit ownership/grant migration; do not solve this by running the pipeline as ACCOUNTADMIN.

## 3. Prepare Python locally

Open PowerShell in the project folder. For this machine:

~~~powershell
Set-Location 'C:\Users\User\OneDrive - Brunel University London\Desktop\Fastmarkets'
~~~

A .venv was created during the local implementation checks. You can use it directly. On a fresh clone, install Python 3.12 and create one:

~~~powershell
py -3.12 -m venv .venv
~~~

Install the tested dependency set:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\dbt.exe --version
~~~

The top-level dependencies are in requirements.txt. The lock file records the locally tested Windows/Python 3.12 environment. Calling the executables directly avoids PowerShell activation-policy issues.

## 4. Create and register a key pair

Run locally:

~~~powershell
.\.venv\Scripts\python.exe tools/create_key.py
~~~

Choose a private-key passphrase and keep it in your password manager. The tool creates an encrypted .secrets/snowflake_key.p8 and prints a public key. It refuses to overwrite an existing key.

In a Snowflake SQL editor, as ACCOUNTADMIN, run this after replacing only the public-key placeholder with the single line printed by the tool:

~~~sql
USE ROLE ACCOUNTADMIN;
SET setup_user = CURRENT_USER();
ALTER USER IDENTIFIER($setup_user)
    SET RSA_PUBLIC_KEY = 'PASTE_PUBLIC_KEY_HERE';
~~~

The private key stays on your machine. Do not upload it to a worksheet or GitHub. This setup uses your trial user with a restricted execution role, not a new service-account deployment.

## 5. Set local connection variables

In the same PowerShell session:

~~~powershell
$env:SNOWFLAKE_ACCOUNT = 'YOUR_ORGANIZATION-YOUR_ACCOUNT'
$env:SNOWFLAKE_USER = 'YOUR_SNOWFLAKE_LOGIN_NAME'
$env:SNOWFLAKE_PRIVATE_KEY_PATH = (Resolve-Path '.secrets/snowflake_key.p8').Path
$keySecret = Read-Host 'Private-key passphrase' -AsSecureString
$keyCredential = [System.Management.Automation.PSCredential]::new('key', $keySecret)
$env:DBT_ENV_SECRET_PRIVATE_KEY_PASSPHRASE = $keyCredential.GetNetworkCredential().Password
$env:DBT_SEND_ANONYMOUS_USAGE_STATS = 'false'
~~~

Use your Snowflake login name, which may differ from your email. Re-run this step when you open a new terminal. The dbt profile reads these variables and contains no credentials.

Check connectivity:

~~~powershell
.\.venv\Scripts\dbt.exe debug --project-dir dbt --profiles-dir dbt
~~~

Proceed only when the connection check succeeds. If it fails, check the account identifier, login name, public-key registration and passphrase before changing the models.

## 6. Load the CSV

First validate the supplied local file without a Snowflake connection:

~~~powershell
.\.venv\Scripts\python.exe loader.py --file homework.csv --validate-only
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

Then load it:

~~~powershell
.\.venv\Scripts\python.exe loader.py --file homework.csv
~~~

Expected source_rows and rows_loaded: 1000. Record the returned SHA-256 and query IDs as run evidence.

The script uploads the file using PUT to a temporary table stage, uses COPY to load a candidate, checks every row was loaded, and publishes HOMEWORK.RAW.HOMEWORK_OBT. You do not need Snowflake's manual CSV upload wizard.

The brief specifically requests a download from the original URL. Once you recover that link, run:

~~~powershell
$env:HOMEWORK_CSV_URL = 'PASTE_THE_ORIGINAL_HTTPS_DOWNLOAD_URL'
.\.venv\Scripts\python.exe loader.py
~~~

The URL must return CSV bytes, not a login/share-page HTML document. Header validation rejects HTML. The original URL was not supplied in this conversation, so the real download route has not been exercised. If the source is unchanged, compare its SHA-256 with the local file's hash.

## 7. Inspect raw data, then build the missing tables

In Snowflake, paste and run profiling.sql. It selects HOMEWORK_ENGINEER and HOMEWORK_WH itself.

Back in local PowerShell:

~~~powershell
.\.venv\Scripts\dbt.exe parse --project-dir dbt --profiles-dir dbt
.\.venv\Scripts\dbt.exe build --project-dir dbt --profiles-dir dbt
~~~

No dbt init, dbt deps or manual table creation is needed. This project has no external dbt packages. Do not continue on a failed build: inspect the first failing model/test and its SQL in dbt/target.

The build creates these tables in HOMEWORK.MARTS:
- DIM_CUSTOMER
- DIM_PRODUCT
- FCT_ORDERS
- FCT_ORDER_ITEMS

It also creates AGG_WEEKLY_PRODUCT as a view, and three staging views in HOMEWORK.STAGING. dbt build executes the data tests and the synthetic weekly unit test.

## 8. Verify outputs and rerun behaviour

In Snowflake, paste and run verify.sql.

Expected results for the supplied snapshot:

| Check | Expected |
| --- | --- |
| Raw rows / customers / orders | 1000 each |
| Products | 3 |
| Order items | 1674 |
| Weeks / week-product rows | 144 / 424 |
| Winning weeks A1 / B1 / C1 | 1 / 139 / 4 |
| NULL phones / emails | 100 / 87 |

For week_start = 2024-05-27, A1 must be flagged as the winner, with revenue 500. B1 has 450 and C1 has 400.

Run the loader and full dbt build again, then rerun verify.sql. Counts and business results should remain unchanged. Record both actual build outcomes in evidence/VALIDATION.md.

Generate and browse documentation locally:

~~~powershell
.\.venv\Scripts\dbt.exe docs generate --project-dir dbt --profiles-dir dbt
.\.venv\Scripts\dbt.exe docs serve --project-dir dbt --profiles-dir dbt --port 8080
~~~

The documentation includes model/column descriptions and lineage. Stop the local server with Ctrl+C.

## 9. Create reviewer access

Only after the successful build, run reviewer_access.sql in Snowflake. It creates a dedicated read-only role and warehouse and grants SELECT on exactly the five submitted objects.

Create the reviewer user separately in a private worksheet. Replace the password below with a unique generated temporary password. Do not save the populated statement in the repository.

~~~sql
USE ROLE ACCOUNTADMIN;
CREATE USER HOMEWORK_REVIEWER
    TYPE = PERSON
    PASSWORD = 'REPLACE_WITH_UNIQUE_TEMPORARY_PASSWORD'
    DEFAULT_ROLE = HOMEWORK_REVIEWER_ROLE
    DEFAULT_WAREHOUSE = REVIEWER_WH
    MUST_CHANGE_PASSWORD = TRUE;
GRANT ROLE HOMEWORK_REVIEWER_ROLE TO USER HOMEWORK_REVIEWER;
~~~

The reviewer must change the temporary password and complete any required MFA enrolment on their own first sign-in. Coordinate this with them; do not bind their account's MFA to your phone. A password alone may not satisfy the trial's authentication policy.

To test role permissions using your own account:

~~~sql
USE ROLE ACCOUNTADMIN;
SET setup_user = CURRENT_USER();
GRANT ROLE HOMEWORK_REVIEWER_ROLE TO USER IDENTIFIER($setup_user);
USE ROLE HOMEWORK_REVIEWER_ROLE;
USE SECONDARY ROLES NONE;
USE WAREHOUSE REVIEWER_WH;

SELECT * FROM HOMEWORK.MARTS.AGG_WEEKLY_PRODUCT LIMIT 10;
SELECT COUNT(*) FROM HOMEWORK.MARTS.FCT_ORDER_ITEMS;
~~~

Both SELECTs must succeed. Run the next two statements separately; each must fail with an access/authorization error. The DELETE condition deliberately matches no rows even if permissions are accidentally too broad.

~~~sql
SELECT * FROM HOMEWORK.RAW.HOMEWORK_OBT LIMIT 1;
DELETE FROM HOMEWORK.MARTS.FCT_ORDERS WHERE FALSE;
~~~

If either succeeds, inspect the role hierarchy and PUBLIC grants. Do not claim least privilege until this is resolved.

Remove the temporary test assignment:

~~~sql
USE ROLE ACCOUNTADMIN;
SET setup_user = CURRENT_USER();
REVOKE ROLE HOMEWORK_REVIEWER_ROLE FROM USER IDENTIFIER($setup_user);
SHOW GRANTS TO ROLE HOMEWORK_REVIEWER_ROLE;
SHOW GRANTS TO USER HOMEWORK_REVIEWER;
~~~

Model replacement uses copy_grants. Rerun reviewer_access.sql and repeat permission checks after your final build. Role tests do not prove that the reviewer's password/MFA login works; confirm that sign-in separately with the reviewer.

## 10. Prepare the repository and submission

Read README.md and docs/AI_WORKFLOW.md and make sure you can explain every decision. Add genuine earlier AI interactions if you have them. Record actual live outcomes in evidence/VALIDATION.md; do not replace pending steps with invented passes.

The project is not yet a Git repository. If Git is installed:

~~~powershell
git init
git add .
git status
git diff --cached --stat
git commit -m "Build Snowflake orders pipeline with dbt models and tests"
~~~

Before committing, confirm .secrets, .venv, logs, private credentials and generated dbt artifacts are excluded. The source CSV is currently included; use a private repository if distribution of the supplied data has not been agreed.

Create an empty GitHub repository in your browser, then use its actual URL:

~~~powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
~~~

Alternatively use GitHub Desktop to add and publish this existing folder. If private, grant the reviewers repository access.

Send:
1. Repository link.
2. Snowflake account URL.
3. HOMEWORK_REVIEWER username and temporary password, through a private channel.
4. A short note about first-login password change/MFA and HOMEWORK.MARTS.AGG_WEEKLY_PRODUCT.

Keep the trial active through the presentation. Remove the reviewer user/role/warehouse when access is no longer needed.

## Troubleshooting

- **Role not authorized:** bootstrap.sql grants HOMEWORK_ENGINEER to CURRENT_USER(). Ensure that is the login name in your environment variables.
- **JWT/key error:** check the account identifier, key file, passphrase and registered public key. Do not paste private-key material into a chat or issue.
- **Object does not exist:** run bootstrap.sql first, then the loader, then dbt build.
- **Insufficient ownership on existing objects:** inspect their owner with an administrator. The new pipeline role must own its raw table and generated dbt objects to replace them.
- **CSV header error:** confirm the file is the original CSV rather than an HTML download page.
- **dbt build fails:** inspect the first failure and dbt/logs/dbt.log. Do not skip the failed test to get a green run.
- **Snowsight navigation differs:** use a SQL editor in Workspaces/Worksheets. All required setup is SQL and does not depend on the manual data-loading UI.

## References

- [Snowflake key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Python connector connections](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect)
- [Snowflake INSERT OVERWRITE](https://docs.snowflake.com/en/sql-reference/sql/insert)
- [dbt build](https://docs.getdbt.com/reference/commands/build)
- [Snowflake authentication changes](https://docs.snowflake.com/en/user-guide/security-mfa-rollout)
