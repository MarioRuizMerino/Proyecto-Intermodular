from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from getpass import getpass
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk
import json
import os

#======== PROVINCIAS =========

PROVINCIAS = {
    "Málaga": "malaga",
    "Sevilla": "sevilla",
    "Cádiz": "cadiz",
    "Huelva": "huelva",
    "Córdoba": "cordoba",
    "Granada": "granada",
    "Jaén": "jaen",
    "Almería": "almeria",
}

def construir_urls(slug_provincia):
    base = f"https://educacionadistancia.juntadeandalucia.es/centros/{slug_provincia}"
    return (
        f"{base}/login/index.php",  # MOODLE_URL
        base                        # MOODLE_BASE
    )

def seleccionar_provincia():
    ventana = tk.Tk()
    ventana.title("Selecciona provincia")

    tk.Label(ventana, text="Provincia:").pack(padx=10, pady=5)

    provincia_var = tk.StringVar()
    combo = ttk.Combobox(ventana, textvariable=provincia_var, state="readonly")
    combo["values"] = list(PROVINCIAS.keys())
    combo.current(0) 
    combo.pack(padx=10, pady=5)

    def confirmar():
        ventana.selected_provincia = provincia_var.get()
        ventana.destroy()

    tk.Button(ventana, text="Aceptar", command=confirmar).pack(padx=10, pady=10)

    ventana.mainloop()
    return getattr(ventana, "selected_provincia", None)

# ===================== SELECCIÓN DE PROVINCIA =====================

provincia_nombre = seleccionar_provincia()
if provincia_nombre is None:
    raise SystemExit("No se seleccionó provincia")

slug = PROVINCIAS[provincia_nombre]
MOODLE_URL, MOODLE_BASE = construir_urls(slug)
print("Usando provincia:", provincia_nombre, "->", MOODLE_BASE)
username = os.environ.get("USERNAME")
COOKIES_PATH = fr"C:\Users\{username}\moodle_cookies.json"

# Pedir credenciales
USERNAME = input("Pon tu usuario: ")
PASSWORD = getpass("Pon tu contraseña: ")

# === SETUP SELENIUM ===
chrome_options = Options()
# Si quieres que no se vea el navegador, descomenta:
# chrome_options.add_argument("--headless=new")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# ======= LOGIN EN MOODLE (CAS) =======
driver.get(MOODLE_URL)

# Botón "Acceso Único Educación"
cas_button = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
cas_button.click()

# Usuario y contraseña CAS
driver.find_element(By.ID, "username").send_keys(USERNAME)
driver.find_element(By.ID, "password").send_keys(PASSWORD)

# Enviar formulario
driver.find_element(By.NAME, "submit").click()

print("Ya casi estás!")

# ======= GUARDAR COOKIES (OPCIONAL) =======
cookies = driver.get_cookies()
with open(COOKIES_PATH, "w", encoding="utf-8") as f:
    json.dump(cookies, f, indent=4, ensure_ascii=False)

print(f"Cookies guardadas en: {COOKIES_PATH}")

# ======= IR AL ÁREA PERSONAL CON SELENIUM =======
driver.get(f"{MOODLE_BASE}/my/")
print("URL actual en Selenium:", driver.current_url)
html_home = driver.page_source
print(html_home[:1000])  # Solo para depurar

# ======= PARSEAR CURSOS =======
def parse_courses(html):
    soup = BeautifulSoup(html, "html.parser")
    courses = []
    # Ajusta el selector si tu Moodle usa otra estructura
    for a in soup.select('a[href*="/course/view.php?id="]'):
        name = a.get_text(strip=True)
        href = a["href"]
        courses.append({"name": name, "url": href})
    return courses

courses = parse_courses(html_home)
print("Cursos encontrados:")
for c in courses:
    print("-", c["name"], "->", c["url"])

# ======= OBTENER TAREAS DE CADA CURSO USANDO SELENIUM =======
def get_assignments_html(course_url):
    driver.get(course_url)
    return driver.page_source

def parse_assignments(html):
    soup = BeautifulSoup(html, "html.parser")
    assignments = []
    # En muchos Moodles, las tareas son enlaces a /mod/assign/view.php?id=XXX
    for a in soup.select('a[href*="/mod/assign/view.php?id="]'):
        name = a.get_text(strip=True)
        href = a["href"]
        assignments.append({"name": name, "url": href})
    return assignments

# Construir estructura: cursos + tareas
for c in courses:
    html_course = get_assignments_html(c["url"])
    c["assignments"] = parse_assignments(html_course)

# ======= INTERFAZ TKINTER =======
root = tk.Tk()
root.title("Cursos y tareas - Moodle")

tree = ttk.Treeview(root)
tree["columns"] = ("tipo",)
tree.column("#0", width=300)
tree.column("tipo", width=100)
tree.heading("#0", text="Nombre")
tree.heading("tipo", text="Tipo")

# Insertar cursos y tareas
for c in courses:
    cid = tree.insert("", "end", text=c["name"], values=("Curso",))
    for a in c.get("assignments", []):
        tree.insert(cid, "end", text=a["name"], values=("Tarea",))

tree.pack(fill="both", expand=True)

# Campo modificable (comentarios)
label = tk.Label(root, text="Comentario seleccionado:")
label.pack(anchor="w", padx=5, pady=5)

text = tk.Text(root, height=4)
text.pack(fill="x", padx=5, pady=5)

def on_select(event):
    item = tree.focus()
    name = tree.item(item, "text")
    text.delete("1.0", tk.END)
    text.insert(tk.END, f"Editar comentario para: {name}")

tree.bind("<<TreeviewSelect>>", on_select)

# Importante: no cierres Selenium antes de terminar de scrapear
root.mainloop()

# Cuando cierres la interfaz, ya puedes cerrar el navegador
driver.quit()