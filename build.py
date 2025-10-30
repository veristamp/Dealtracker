import os
import shutil
import random
import string
import pyzipper
from pathlib import Path

# Configuration
CLIENT_DIR = Path("client")
DIST_DIR = Path("dist")
ZIP_PATH = DIST_DIR / "dealtracker-client-secure.zip"

def make_secure_zip(source_dir, zip_path, zip_password):
    """Creates a password-protected zip of the source directory."""
    print(f"[*] Creating secure zip: {zip_path}")
    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(zip_password.encode('utf-8'))
        for folder, _, files in os.walk(source_dir):
            for file in files:
                full_path = Path(folder) / file
                arcname = full_path.relative_to(source_dir.parent)
                zf.write(full_path, str(arcname))

def main():
    """Main build process without PyArmor."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    zip_password = "1cpwyXc3WlZQeQrYrANH"
    make_secure_zip(CLIENT_DIR, ZIP_PATH, zip_password)

    print("\n" + "="*50)
    print("✅ SECURE BUILD SUCCESS ")
    print(f"==> Zip Password: {zip_password} <==")
    print("Copy this password into launcher.py")
    print(f"\nFiles for shipping: {DIST_DIR.resolve()}")
    print("="*50)

if __name__ == "__main__":
    main()
