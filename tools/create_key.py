"""Generate an encrypted local key; print only its public Snowflake value."""

from getpass import getpass
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main():
    directory = Path(__file__).resolve().parents[1] / ".secrets"
    directory.mkdir(exist_ok=True)
    destination = directory / "snowflake_key.p8"
    if destination.exists():
        raise SystemExit("Key already exists. Reuse it; do not overwrite a registered key.")
    password = getpass("New private-key passphrase (at least 16 characters): ")
    if len(password) < 16 or password != getpass("Confirm passphrase: "):
        raise SystemExit("Passphrases must match and contain at least 16 characters.")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    destination.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password.encode()),
    ))
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    print("Private key saved to:", destination)
    print("Public key for RSA_PUBLIC_KEY:")
    print("".join(public.splitlines()[1:-1]))


if __name__ == "__main__":
    main()
