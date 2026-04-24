#!/usr/bin/env python3
"""
Script de build para MoodleAndalucia.
Genera un ejecutable standalone con PyInstaller.

Uso:
    python scripts/build.py

El ejecutable se generará en dist/MoodleAndalucia (Linux) o dist/MoodleAndalucia.exe (Windows).
Nota: el usuario final necesita tener Google Chrome instalado.
"""

import subprocess
import sys
import os
from pathlib import Path


def check_deps():
    """Verifica que todas las dependencias de build estén instaladas."""
    missing = []
    deps = {
        "PyInstaller": "pyinstaller",
        "customtkinter": "customtkinter",
        "selenium": "selenium",
        "webdriver_manager": "webdriver-manager",
        "bs4": "beautifulsoup4",
        "packaging": "packaging",
    }
    for module, package in deps.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print("[ERROR] Faltan las siguientes dependencias:")
        for pkg in missing:
            print(f"  - {pkg}")
        print(f"\nInstálalas con:\n  pip install {' '.join(missing)}")
        sys.exit(1)

    print("[OK] Todas las dependencias están disponibles.")


def main():
    # Moverse a la raíz del proyecto (un nivel arriba de /scripts/)
    root = Path(__file__).resolve().parent.parent
    os.chdir(root)
    print(f"[INFO] Directorio de trabajo: {root}")

    check_deps()

    platform_name = "Windows" if sys.platform.startswith("win") else "Linux"
    print(f"[INFO] Plataforma detectada: {platform_name}")
    print("[BUILD] Generando ejecutable con PyInstaller...\n")

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "MoodleAndalucia.spec", "--clean"],
        check=False,
    )

    print()
    if result.returncode == 0:
        ext = ".exe" if sys.platform.startswith("win") else ""
        out = root / "dist" / f"MoodleAndalucia{ext}"
        print(f"[OK] ¡Build completado!")
        print(f"[OK] Ejecutable en: {out}")
        print(f"\n[NOTA] El usuario final necesita tener Google Chrome instalado.")
    else:
        print("[ERROR] El build falló. Revisa los mensajes anteriores.")
        sys.exit(1)


if __name__ == "__main__":
    main()
