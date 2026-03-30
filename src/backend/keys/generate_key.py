from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import os

# Ensure output directory exists
os.makedirs("D:/keys", exist_ok=True)

# Generate Ed25519 private key
private_key = ed25519.Ed25519PrivateKey.generate()

# Write private key (PKCS8 PEM)
with open("D:/keys/qweather_private.pem", "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )

# Derive public key and write SPKI PEM
public_key = private_key.public_key()
with open("D:/keys/qweather_public.pem", "wb") as f:
    f.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )

print("Key generation complete.")
print("Private key: D:/keys/qweather_private.pem")
print("Public key: D:/keys/qweather_public.pem")