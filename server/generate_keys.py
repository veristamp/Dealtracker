from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from pathlib import Path
import os
import dotenv

dotenv.load_dotenv()

server_dir = Path(__file__).resolve().parent          
repo_root = server_dir.parent                         
files_dir = repo_root / "files"                       
client_dir = repo_root / "client"                     

files_dir.mkdir(parents=True, exist_ok=True)
client_dir.mkdir(parents=True, exist_ok=True)
priv_rel = os.getenv("PRIVATE_KEY_PATH", "files/private.pem")
pub_rel = os.getenv("PUBLIC_KEY_PATH", "files/public.pem")

priv_path = (repo_root / priv_rel).resolve()
pub_path = (repo_root / pub_rel).resolve()
client_pub_path = (client_dir / "public.pem").resolve()

private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
pem_public = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

priv_path.parent.mkdir(parents=True, exist_ok=True)
pub_path.parent.mkdir(parents=True, exist_ok=True)

priv_path.write_bytes(pem_private)
print(f"Ed25519 private key saved to {priv_path}")

pub_path.write_bytes(pem_public)
print(f"Ed25519 public key saved to {pub_path}")

client_pub_path.write_bytes(pem_public)
print(f"Public key copied to {client_pub_path}")

print("\n✅ Done — keys are in the root files/ directory and client/public.pem")
