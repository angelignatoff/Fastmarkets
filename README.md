# Snowflake orders take-home

A local Python loader lands a CSV snapshot in Snowflake. dbt parses the JSON order items, cleans customer contact fields, and builds four tables plus a weekly product view.

Start with [SETUP.md](SETUP.md) for the complete Windows/Snowflake walkthrough.

## Project

| File or directory | Purpose |
| --- | --- |
| `loader.py` | Download or read the CSV, validate it, and load the raw snapshot |
| `bootstrap.sql` | Create the database, schemas, warehouse and engineering role |
| `dbt/models/staging/` | Type conversion, contact cleaning and JSON flattening |
| `dbt/models/marts/` | Customer, Product, Order, OrderItem and weekly aggregation |
| `dbt/tests/` | Data contracts, grain and reconciliation tests |
| `dbt/models/unit_tests.yml` | Synthetic weekly tie and calendar-boundary test |
| `profiling.sql`, `verify.sql` | Independent source probes and final inspection queries |
| `reviewer_access.sql` | Read-only grants on the five submitted objects |
| `tools/profile_csv.py` | Local reference calculation using Python Decimal |
| `tests/` | Local loader validation and failure-path tests |
| `docs/AI_WORKFLOW.md` | Actual prompts, decisions, corrections and validation limits |
| `evidence/` | Local reference results and verification status |

## Model and decisions

The analytical layer is a small dimensional model. Natural source identifiers are adequate for one source. A Data Vault would add history and integration structures that this exercise does not need.

| Snowflake object in HOMEWORK.MARTS | Grain | Materialization |
| --- | --- | --- |
| DIM_CUSTOMER | One customer | Table |
| DIM_PRODUCT | One product code | Table |
| FCT_ORDERS | One order | Table |
| FCT_ORDER_ITEMS | One order and JSON array position | Table |
| AGG_WEEKLY_PRODUCT | One Monday-start week and product with sales | View |

OrderItem uses the array index to preserve repeated appearances of a product in an order. The combined key is `order_id:line_number`; array reordering may change it. This is suitable for a rebuilt snapshot, not a durable line identifier for change capture.

Customer and product names use the latest observed order attributes, with deterministic tie-breakers. This is Type 1/current-state behaviour, not reconstructed history. The single source currently has one customer per order, but the model permits repeat customers.

Prices belong to order lines. They use fixed-point decimals, as do order totals and revenue. Currency is absent from the source: the project assumes one currency and does not invent USD or GBP. Order totals remain independent of line totals and are reconciled within 0.01. Do not sum header totals after joining orders to items.

The source contract assumes positive whole quantities and nonnegative monetary values with at most two decimal places. Returns and fractional quantities require an explicit rule change.

Top seller means highest revenue, not most units. Every tied leader receives `is_top_seller = 1`; all other products that sold that week receive 0. The view also reports units and distinct orders. Products with zero sales are absent. Order counts are not additive across products. Monday dates are calculated with DAYOFWEEKISO, independently of the session's WEEK_START setting.

## Loading and transformation

Python runs locally because downloading and uploading a file needs little infrastructure. SQL transformations live in dbt and execute in Snowflake. Key-pair authentication avoids storing Snowflake login passwords in scripts.

Raw fields remain text, including the JSON string and dirty contact values. The loader validates the header, field counts and nonempty JSON arrays, then uses strict COPY into a temporary candidate. Only a complete, row-count-checked load is published using one INSERT OVERWRITE statement. This preserves the existing raw snapshot on download/COPY/validation failure. It is a replaceable snapshot, not immutable history.

The loader prints a source SHA-256, row counts and Snowflake query IDs. A successful raw load does not establish business validity: dbt tests check types, identifiers, item fields and reconciliation. Failed dbt runs are not accepted as a completed release.

All marts rebuild in full. At 1,000 orders, this is easier to explain and correctly handles corrected or removed historical rows. Incremental modelling would require a source change timestamp, deletion policy and durable line identifiers.

The schema macro deliberately targets STAGING and MARTS in this dedicated trial database. It is not a shared multi-developer deployment design.

## Source findings

The supplied CSV was independently checked locally. Results are reproducible with:

```powershell
.\.venv\Scripts\python.exe tools/profile_csv.py --output evidence/local_profile.json
```

- 1,000 orders, 1,000 customers and three products.
- 1,674 order items; no repeated product within an order in this snapshot.
- Dates from 2023-01-01 to 2025-09-26.
- 144 Monday-start weeks and 424 week/product rows.
- Exact reconciliation of all source order totals.
- Revenue winners: A1 in one week, B1 in 139 weeks, C1 in four weeks; no ties.
- The documented cleaning rules yield 100 missing phones and 87 missing emails.

Contact validation is deliberately basic. Known phone sentinels become NULL; other phone strings are retained without claiming full international-number validation. Invalid emails become NULL without removing the customer's orders.

## Validation and AI

See [AI_WORKFLOW.md](docs/AI_WORKFLOW.md) for the actual workflow and [VALIDATION.md](evidence/VALIDATION.md) for what has and has not run.

Local checks do not prove that Snowflake has built the models. Before submitting, complete the live load, dbt build, repeat-run checks and reviewer permissions checks in SETUP.md.

## Scope beyond the core

Implemented: strict candidate loading, safe raw publication, repeatable full rebuilds, environment-based authentication, query tags, data tests, a synthetic weekly unit test and scoped reviewer grants.

Next in a production setting:
- Run the Python loader and dbt as an ordered scheduled job with failure notifications.
- Record load hashes and execution results in a durable audit table.
- Gate publication of all marts together; dbt currently replaces models individually, so a failed build can leave a mixture of old and new tables.
- Add volume/contact-quality trend monitoring.
- Measure query profiles and change behaviour before choosing incremental processing.
- Add a semantic layer only after defining currency and agreeing the revenue/units vocabulary.

Compute uses XSMALL warehouses with 60-second auto-suspend. No scale benchmark or cost guarantee is claimed. Cortex and orchestration are proposals, not implemented features.

## Submission

Publish this repository, complete the live checks, and provide the Snowflake account URL and dedicated reviewer credentials privately. No passwords or private keys belong in Git. The local CSV path is supported; the brief's URL-download demonstration remains pending until the original link is recovered.
