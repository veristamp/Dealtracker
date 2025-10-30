import os
import sys
import tempfile
import subprocess
import pyzipper
from pathlib import Path
import shutil

ZIP_PASSWORD = "1cpwyXc3WlZQeQrYrANH"

def find_venv_python():
    """Finds the python executable inside the venv."""
    if getattr(sys, 'frozen', False):
        here = os.path.dirname(sys.executable)
    else:
        here = os.path.dirname(os.path.abspath(__file__))
    
    win_py = os.path.join(here, "dealtracker-venv", "Scripts", "python.exe")
    posix_py = os.path.join(here, "dealtracker-venv", "bin", "python3")
    
    if os.path.exists(win_py):
        return win_py
    elif os.path.exists(posix_py):
        return posix_py
    else:
        print(f"[ERROR] Could not locate dealtracker-venv Python in '{here}'.")
        input("Press Enter to exit...")
        sys.exit(1)

def main():
    if not Path("activated.txt").exists():
        print("[ERROR] Environment not activated! Run setup.bat first.")
        input("Press Enter to exit...")
        sys.exit(1)

    VENV_PYTHON = find_venv_python()
    ZIP_FILE = "dealtracker-client-secure.zip"
    temp_root = Path(tempfile.gettempdir()) / f"dealtracker_simple_{os.getpid()}"

    try:
        if temp_root.exists():
            shutil.rmtree(temp_root)
        temp_root.mkdir()

        print("[*] Extracting secure client code...")
        with pyzipper.AESZipFile(ZIP_FILE) as zf:
            zf.pwd = ZIP_PASSWORD.encode('utf-8')
            zf.extractall(path=str(temp_root))

        print("[*] Launching DealTracker FastAPI app...")
        
        subprocess.run([
            VENV_PYTHON, "-m", "client.main"
        ], cwd=str(temp_root))

    except KeyboardInterrupt:
        print("\n[*] Shutting down DealTracker...")
    except Exception as e:
        print(f"[ERROR] Launch failed: {e}")
    finally:
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)
        print("[*] Cleaned up temporary directory.")

if __name__ == "__main__":
    main()
