import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from loader import COLUMNS, fetch_csv, load_snapshot, validate_csv


class CsvValidationTests(unittest.TestCase):
    def check(self, rows, header=COLUMNS):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerows(rows)
            return validate_csv(path)

    def row(self, items='[{"product_id":"A","quantity":1,"price":1}]'):
        return ["1", "Name", '"+44-000"', "a@example.test", "1", "2024-01-01", "1", items]

    def test_valid_quoted_json(self):
        self.assertEqual(self.check([self.row()]), 1)

    def test_bad_header_rejected(self):
        with self.assertRaises(ValueError):
            self.check([self.row()], tuple(reversed(COLUMNS)))

    def test_wrong_field_count_rejected(self):
        with self.assertRaises(ValueError):
            self.check([self.row() + ["extra"]])

    def test_empty_file_rejected(self):
        with self.assertRaises(ValueError):
            self.check([])

    def test_invalid_json_or_array_rejected(self):
        for value in ("[", "{}", "null", "[]"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.check([self.row(value)])

    def test_supplied_csv(self):
        self.assertEqual(validate_csv(Path(__file__).resolve().parents[1] / "homework.csv"), 1000)

    def test_download_uses_https_and_copies_bytes(self):
        response = MagicMock()
        response.url = "https://example.test/homework.csv"
        response.read.side_effect = [b"csv bytes", b""]
        response.__enter__.return_value = response
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "download.csv"
            with patch("loader.urlopen", return_value=response) as request:
                fetch_csv(response.url, path)
            self.assertEqual(path.read_bytes(), b"csv bytes")
            request.assert_called_once_with(response.url, timeout=60)

    def test_non_https_url_rejected(self):
        with self.assertRaises(ValueError):
            fetch_csv("http://example.test/file.csv", Path("unused.csv"))


class PublicationTests(unittest.TestCase):
    def cursor(self, rows_loaded=1, count=1, errors=0, status="LOADED"):
        cursor = MagicMock()
        cursor.description = [(name,) for name in ("status", "errors_seen", "rows_loaded")]
        cursor.fetchall.return_value = [(status, errors, rows_loaded)]
        cursor.fetchone.return_value = (count,)
        cursor.execute.return_value = cursor
        return cursor

    def run_load(self, cursor):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        with patch("loader.connection_options", return_value={}), \
                patch("snowflake.connector.connect", return_value=connection):
            return load_snapshot(Path("homework.csv"), 1)

    def test_publish_only_after_copy_and_count(self):
        cursor = self.cursor()
        self.run_load(cursor)
        statements = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertTrue(statements[-1].startswith("INSERT OVERWRITE"))
        self.assertTrue(any(sql.startswith("SELECT COUNT") for sql in statements[:-1]))
        self.assertFalse(any("TRUNCATE" in sql or "CREATE OR REPLACE" in sql for sql in statements))

    def test_failed_validation_never_publishes(self):
        for kwargs in ({"rows_loaded": 0}, {"count": 0}, {"errors": 1}, {"status": "PARTIALLY_LOADED"}):
            with self.subTest(kwargs=kwargs):
                cursor = self.cursor(**kwargs)
                with self.assertRaises(RuntimeError):
                    self.run_load(cursor)
                self.assertFalse(any("INSERT OVERWRITE" in call.args[0]
                                     for call in cursor.execute.call_args_list))

    def test_copy_failure_never_publishes(self):
        cursor = self.cursor()
        def execute(sql):
            if sql.lstrip().startswith("COPY INTO"):
                raise RuntimeError("Simulated COPY failure")
            return cursor
        cursor.execute.side_effect = execute
        with self.assertRaises(RuntimeError):
            self.run_load(cursor)
        self.assertFalse(any("INSERT OVERWRITE" in call.args[0]
                             for call in cursor.execute.call_args_list))


if __name__ == "__main__":
    unittest.main()
