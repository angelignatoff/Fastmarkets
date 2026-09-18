"""Export registration SQL for an existing encrypted key without changing it."""

import argparse
import base64
from getpass import getpass
import hashlib
import os
from pathlib import Path
import re

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def registration(private_bytes: bytes, password: str, user: str) -> tuple[str, str]:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", user):
        raise ValueError("Use an unquoted Snowflake user identifier, such as IGNATOFF")
    key = serialization.load_pem_private_key(private_bytes, password=password.encode())
    if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
        raise ValueError("Expected an RSA private key of at least 2048 bits")
    public_der = key.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_value = base64.b64encode(public_der).decode("ascii")
    fingerprint = "SHA256:" + base64.b64encode(hashlib.sha256(public_der).digest()).decode("ascii")
    sql = ("USE ROLE ACCOUNTADMIN;\n"
           f"ALTER USER {user.upper()} SET RSA_PUBLIC_KEY = '{public_value}';\n"
           f"DESC USER {user.upper()};\n")
    return sql, fingerprint


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", required=True)
    parser.add_argument("--key", type=Path, default=Path(os.environ.get(
        "SNOWFLAKE_PRIVATE_KEY_PATH", root / ".secrets" / "snowflake_key.p8")))
    args = parser.parse_args()
    if not args.key.is_file():
        parser.error(f"Key not found: {args.key}. Run tools/create_key.py first or supply --key.")
    password = getpass("Existing private-key passphrase: ")
    try:
        sql, fingerprint = registration(args.key.read_bytes(), password, args.user)
    except (ValueError, TypeError) as exc:
        parser.exit(1, f"Cannot export public key: {exc}\n")
    output = root / ".secrets" / "register_public_key.sql"
    output.parent.mkdir(exist_ok=True)
    output.write_text(sql, encoding="utf-8")
    print(f"Registration SQL saved to: {output}")
    print(f"Expected RSA_PUBLIC_KEY_FP: {fingerprint}")
    print("Copy the complete SQL file into Snowflake and execute it.")
    print("Only public-key material is in that SQL file. The private key is unchanged.")


if __name__ == "__main__":
    main()
