"""Load a validated CSV snapshot into HOMEWORK.RAW.HOMEWORK_OBT."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen
import uuid

COLUMNS = (
    "customer_id", "customer_name", "customer_phone", "customer_email",
    "order_id", "order_date", "order_total", "order_items",
)


def validate_csv(path: Path) -> int:
    count = 0
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        if next(reader, None) != list(COLUMNS):
            raise ValueError("CSV header must match the eight homework columns in order")
        for row in reader:
            count += 1
            if len(row) != len(COLUMNS):
                raise ValueError(f"Record {count}: expected eight fields")
            try:
                items = json.loads(row[7])
            except json.JSONDecodeError as exc:
                raise ValueError(f"Record {count}: invalid order_items JSON") from exc
            if not isinstance(items, list) or not items:
                raise ValueError(f"Record {count}: order_items must be a nonempty array")
    if not count:
        raise ValueError("CSV contains no data rows")
    return count


def fetch_csv(url: str, destination: Path) -> None:
    if urlparse(url).scheme != "https":
        raise ValueError("The source URL must use HTTPS")
    with urlopen(url, timeout=60) as response:
        if urlparse(response.url).scheme != "https":
            raise ValueError("The source redirected away from HTTPS")
        with destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)


def connection_options() -> dict:
    required = ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH",
                "DBT_ENV_SECRET_PRIVATE_KEY_PASSPHRASE")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise ValueError("Missing environment variables: " + ", ".join(missing))
    return {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "authenticator": "SNOWFLAKE_JWT",
        "private_key_file": os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
        "private_key_file_pwd": os.environ["DBT_ENV_SECRET_PRIVATE_KEY_PASSPHRASE"],
        "role": "HOMEWORK_ENGINEER",
        "warehouse": "HOMEWORK_WH",
        "database": "HOMEWORK",
        "schema": "RAW",
        "session_parameters": {"QUERY_TAG": "homework:loader"},
    }


def load_snapshot(path: Path, expected_rows: int) -> dict:
    import snowflake.connector

    candidate = "HOMEWORK.RAW.LOAD_" + uuid.uuid4().hex.upper()
    definition = ", ".join(f"{name} VARCHAR" for name in COLUMNS)
    with snowflake.connector.connect(**connection_options()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE TEMPORARY TABLE {candidate} ({definition})")
            stage = "@%" + candidate.rsplit(".", 1)[1]
            file_uri = ("file://" + path.resolve().as_posix()).replace("'", "''")
            cursor.execute(f"PUT '{file_uri}' {stage} AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
            cursor.execute(f"""
                COPY INTO {candidate} FROM {stage}
                FILE_FORMAT = (
                    TYPE=CSV SKIP_HEADER=1 FIELD_OPTIONALLY_ENCLOSED_BY='"'
                    ESCAPE_UNENCLOSED_FIELD=NONE EMPTY_FIELD_AS_NULL=FALSE
                    NULL_IF=() ERROR_ON_COLUMN_COUNT_MISMATCH=TRUE
                    SKIP_BYTE_ORDER_MARK=TRUE ENCODING='UTF8'
                )
                ON_ERROR=ABORT_STATEMENT
            """)
            copy_query_id = cursor.sfqid
            names = [column[0].lower() for column in cursor.description]
            results = [dict(zip(names, row)) for row in cursor.fetchall()]
            if (not results or any(row["status"] != "LOADED" or row["errors_seen"]
                                   for row in results)
                    or sum(row["rows_loaded"] for row in results) != expected_rows):
                raise RuntimeError("COPY did not load every source row; snapshot unchanged")
            actual_rows = cursor.execute(f"SELECT COUNT(*) FROM {candidate}").fetchone()[0]
            if actual_rows != expected_rows:
                raise RuntimeError("Source and candidate counts differ; snapshot unchanged")

            cursor.execute(f"CREATE TABLE IF NOT EXISTS HOMEWORK.RAW.HOMEWORK_OBT ({definition})")
            # One DML statement publishes without an empty-table interval.
            cursor.execute(f"INSERT OVERWRITE INTO HOMEWORK.RAW.HOMEWORK_OBT SELECT * FROM {candidate}")
            return {"rows_loaded": actual_rows, "copy_query_id": copy_query_id,
                    "publish_query_id": cursor.sfqid}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--url", help="Original HTTPS download URL")
    source.add_argument("--file", type=Path, help="Local CSV for offline development")
    parser.add_argument("--validate-only", action="store_true", help="Check CSV without connecting")
    args = parser.parse_args()
    url = args.url or (os.environ.get("HOMEWORK_CSV_URL") if not args.file else None)
    if not args.file and not url:
        parser.error("Provide --url, HOMEWORK_CSV_URL, or --file homework.csv")

    with tempfile.TemporaryDirectory(prefix="homework_") as directory:
        path = Path(directory) / "homework.csv"
        if args.file:
            shutil.copyfile(args.file, path)
        else:
            fetch_csv(url, path)
        count = validate_csv(path)
        report = {"source": "local" if args.file else "https", "source_rows": count,
                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if not args.validate_only:
            report.update(load_snapshot(path, count))
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
