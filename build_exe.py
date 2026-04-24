"""
ATENCIÓN: Este archivo se mantiene por compatibilidad.
Usa el nuevo script de build en su lugar:

    python scripts/build.py

El nuevo script es multiplataforma (Windows y Linux) y usa el .spec actualizado.
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    nuevo = Path(__file__).parent / "scripts" / "build.py"
    print(f"[INFO] Redirigiendo a {nuevo} ...")
    subprocess.run([sys.executable, str(nuevo)], check=False)