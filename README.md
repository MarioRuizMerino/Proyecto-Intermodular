# Proyecto-Intermodular

Este es el trabajo que hemos creado los siguientes integrantes para el trabajo de Proyecto Intermodular:
* Mario Ruiz Merino
* Marco Garcia Carrasco
* Fabio Martín Muñoz
* Manuel Torres Urbano

En este proyecto nos hemos propuesto a llevar a cabo un proyecto, para que las personas que no tengan tanto conocimiento de la Moodle, puedan usarla más accesiblemente.

Para ello, estamos creando este ejecutable, que la gente se descargaría y pondría en su ordenador, y tendría una interfaz bonita y amigable de la moodle, en este instante, lo estamos enfocando a la Moodle de Andalucía, pero en un futuro, podríamos orientarlo a Moodle en general.

---

## 🗂️ Estructura

```
├── main.py              # Punto de entrada
├── src/
│   ├── config.py        # Provincias
│   ├── cache.py         # Caché local
│   ├── scraper.py       # Login y scraping (Selenium + BS4)
│   └── gui.py           # Interfaz gráfica (CustomTkinter)
├── scripts/
│   └── build.py         # Script de build multiplataforma
├── MoodleAndalucia.spec # Configuración PyInstaller
└── requirements.txt
```

## 🚀 Desarrollo

```bash
pip install -r requirements.txt
python main.py
```

> Requiere **Google Chrome** instalado.

## 🔨 Generar ejecutable

```bash
pip install pyinstaller
python scripts/build.py
```

- **Linux:** `dist/MoodleAndalucia`
- **Windows:** `dist/MoodleAndalucia.exe`

> El ejecutable no requiere Python. Solo necesita Google Chrome instalado.
