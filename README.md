# Snowflake orders take-home

`pipe.ipynb` downloads the source CSV and loads it inside Snowflake. dbt then parses the JSON order items and builds customer, product, order and order-item tables, plus a weekly product aggregation view.

Follow [SETUP.md](SETUP.md) to run the project. The original [loader.py](loader.py) is retained as a local command-line alternative.

**Trial account:** Snowflake disables external access by default, which prevents the notebook from downloading the CSV inside Snowflake. Use `loader.py` locally for the URL download and load, followed by the same dbt build. The notebook requires an account with external access enabled. See [Snowflake's limitation](https://docs.snowflake.com/en/developer-guide/external-network-access/external-network-access-limitations).

## Project files

| Path | Purpose |
| --- | --- |
| `pipe.ipynb` | Main loader: URL download, validation, staged COPY and raw publication |
| `bootstrap.sql` | Database, schemas, warehouse and engineering role |
| `dbt/` | Models, macros, tests, documentation and connection profile |
| `profiling.sql`, `verify.sql` | Source exploration and final result checks |
| `reviewer_access.sql` | Read-only access to the five final objects |
| `loader.py`, `tests/test_loader.py` | Original local loader and its tests |
| `tools/` | Key-pair setup and independent CSV profiling |
| `evidence/` | Reference results and validation notes |
| `docs/AI_WORKFLOW.md` | AI workflow summary |

## Modelling decisions

The project uses a small dimensional model. Natural source identifiers are sufficient for this single source; full rebuilds are appropriate for 1,000 orders and handle corrected or removed historical rows without incremental-load bookkeeping.

| Object in `HOMEWORK.MARTS` | Grain | Type |
| --- | --- | --- |
| `DIM_CUSTOMER` | One customer | Table |
| `DIM_PRODUCT` | One product code | Table |
| `FCT_ORDERS` | One order | Table |
| `FCT_ORDER_ITEMS` | One order and JSON array position | Table |
| `AGG_WEEKLY_PRODUCT` | One Monday-start week and product with sales | View |

Order-item keys combine order ID and array position, preserving repeated products within an order. Reordering the source array can change these keys, so they are snapshot identifiers rather than durable change-tracking keys.

Customer and product descriptions use the latest observed order attributes (Type 1). Phone sentinels and invalid email formats become NULL without removing orders. Prices remain on order lines and use fixed-point decimals. The source has no currency field, so calculations assume one unspecified currency. Header totals reconcile to line totals within 0.01; do not sum header totals after joining to multiple lines.

**Top seller means highest revenue.** All tied leaders receive `is_top_seller = 1`; other products that sold that week receive 0. Weeks start on Monday independently of the session's `WEEK_START` setting. The view also includes units and distinct order counts. Products with no sales are absent, and order counts must not be added across products.

## Execution and validation

The notebook uses Snowflake's active Snowpark session, keeping ingestion visible without separate local credentials. It validates the CSV header and JSON arrays, loads a temporary candidate with strict COPY, checks counts and publishes with one `INSERT OVERWRITE`. Raw values stay as text for dbt to parse and validate. dbt runs from the local terminal using key-pair authentication and executes its SQL in Snowflake.

Tests cover source contracts, uniqueness, relationships, order reconciliation and weekly results. A synthetic unit test covers ties, repeated product lines and a week crossing the year boundary. An independent Python calculation provides a reference in [evidence/local_profile.json](evidence/local_profile.json); execution status is recorded in [evidence/VALIDATION.md](evidence/VALIDATION.md).

Expected results for the supplied snapshot: **1,000 orders, 1,000 customers, 3 products, 1,674 items and 424 week/product rows across 144 weeks**. For the week beginning 2024-05-27, revenues are A1 = 500, B1 = 450 and C1 = 400, making A1 the winner.

## Operational choices

Candidate loading protects the current raw snapshot if download, validation or COPY fails. Repeated successful loads replace it instead of appending duplicates. XSMALL warehouses use 60-second auto-suspend. Secrets stay outside Git, and reviewer access is limited to the five marts.

With more time, I would schedule ingestion followed by dbt, store load hashes and results in an audit table, and add failure notifications. dbt currently replaces models individually, so a failed build can leave mixed model versions; publishing all marts together would be a further improvement. No scale benchmark or measured cost is claimed.

## Submission

The [AI workflow](docs/AI_WORKFLOW.md) describes the assistance used during the project. Reviewer account details are shared privately; [reviewer_access.sql](reviewer_access.sql) grants the purpose-built role read-only access to the final tables and view.
