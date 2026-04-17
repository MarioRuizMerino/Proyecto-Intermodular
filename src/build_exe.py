import PyInstaller.__main__
import os
import customtkinter
import sys

# Obtener la ruta de customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

# En Windows se usa ';', en Linux/Mac se usa ':'
separator = ';' if sys.platform.startswith('win') else ':'

PyInstaller.__main__.run([
    'main.py',
    '--noconsole',
    '--onefile',
    f'--add-data=src{separator}src',
    f'--add-data={ctk_path}{separator}customtkinter',
    '--name=MoodleAndalucia',
    '--clean'
])