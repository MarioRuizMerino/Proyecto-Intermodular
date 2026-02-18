from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from urllib.parse import urlparse, parse_qs

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
def get_course_id(url):
    qs = parse_qs(urlparse(url).query)
    return qs.get("id", [None])[0]

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
def get_all_assignments_from_index(course_url):
    cid = get_course_id(course_url)

    if not cid:
        return []

    index_url = f"{MOODLE_BASE}/mod/assign/index.php?id={cid}"

    driver.get(index_url)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    assignments = []

    # Tabla oficial de tareas de Moodle
    for row in soup.select("table.generaltable tbody tr"):
        link = row.select_one("a")

        if not link:
            continue

        name = link.get_text(strip=True)
        href = link["href"]

        # Intentar descripción (a veces está en la tabla)
        cols = row.find_all("td")
        description = ""

        if len(cols) > 1:
            description = cols[1].get_text(strip=True)

        assignments.append({
            "name": name,
            "url": href,
            "description": description or ""
        })

    return assignments


def parse_assignments(html):
    soup = BeautifulSoup(html, "html.parser")
    sections = []

    for sec in soup.select("li.section"):

        title_el = (
            sec.select_one(".sectionname") or
            sec.select_one("h3") or
            sec.select_one(".section-title")
        )

        if not title_el:
            continue

        section_title = title_el.get_text(strip=True)
        tasks = []

        for li in sec.select("li.activity.assign"):
            a = li.select_one("a.aalink")

            if not a:
                continue

            name = a.get_text(strip=True)
            href = a["href"]

            # Buscar descripción en varios sitios
            desc_el = (
                li.select_one(".contentafterlink") or
                li.select_one(".no-overflow") or
                li.select_one(".activity-description") or
                li.select_one(".contentwithoutlink")
            )

            description = ""
            if desc_el:
                description = desc_el.get_text(
                    "\n", strip=True)

            tasks.append({
                "name": name,
                "url": href,
                "description": description or ""
            })

        if tasks:
            sections.append({
                "title": section_title,
                "tasks": tasks
            })

    return sections


# Construir estructura: cursos + tareas
for c in courses:
    c["assignments"] = [{
        "title": "Tareas",
        "tasks": get_all_assignments_from_index(c["url"])
    }]



# ======= INTERFAZ TKINTER =======

# ===== TEMAS =====
TEMAS = {
    "oscuro": {
        "BG": "#121212",
        "FG": "#EEEEEE",
        "ACCENT": "#1E88E5",
        "TREE_BG": "#1E1E1E",
        "TEXT_BG": "#1E1E1E"
    },
    "claro": {
        "BG": "#F5F5F5",
        "FG": "#222222",
        "ACCENT": "#1976D2",
        "TREE_BG": "#FFFFFF",
        "TEXT_BG": "#FFFFFF"
    }
}

root = tk.Tk()
root.title("Cursos y tareas - Moodle")
root.geometry("700x500")

style = ttk.Style()
style.theme_use("clam")

# ===== FUNCIÓN CAMBIAR TEMA =====
def aplicar_tema(nombre):
    colores = TEMAS[nombre]

    root.configure(bg=colores["BG"])

    style.configure(".",
                    background=colores["BG"],
                    foreground=colores["FG"])

    style.configure("Treeview",
                    background=colores["TREE_BG"],
                    fieldbackground=colores["TREE_BG"],
                    foreground=colores["FG"])

    style.map("Treeview",
              background=[("selected", colores["ACCENT"])],
              foreground=[("selected", "white")])

    label.configure(bg=colores["BG"], fg=colores["FG"])

    text.configure(bg=colores["TEXT_BG"],
                   fg=colores["FG"],
                   insertbackground=colores["FG"])

# ===== MENÚ SUPERIOR =====
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

menu_tema = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Tema", menu=menu_tema)

menu_tema.add_command(label="Modo oscuro",
                      command=lambda: aplicar_tema("oscuro"))

menu_tema.add_command(label="Modo claro",
                      command=lambda: aplicar_tema("claro"))

# ===== TREEVIEW =====
tree = ttk.Treeview(root)
tree["columns"] = ("tipo",)
tree.column("#0", width=300)
tree.column("tipo", width=100)
tree.heading("#0", text="Nombre")
tree.heading("tipo", text="Tipo")

# Insertar cursos y tareas
for c in courses:
    cid = tree.insert("", "end", text=c["name"], values=("Curso",))

    for sec in c.get("assignments", []):
        sid = tree.insert(cid, "end",
                          text=sec["title"],
                          values=("Sección",))

        for task in sec["tasks"]:
            tree.insert(sid, "end",
                        text=task["name"],
                        values=("Tarea",))


tree.pack(fill="both", expand=True, padx=10, pady=10)

# Campo modificable (comentarios)
label = tk.Label(root, text="Comentario seleccionado:")
label.pack(anchor="w", padx=10, pady=5)

text = tk.Text(root, height=4)
text.pack(fill="x", padx=10, pady=5)

def on_select(event):
    item = tree.focus()
    name = tree.item(item, "text")

    # Buscar descripción
    desc = ""
    for c in courses:
        for a in c.get("assignments", []):
            if a["name"] == name:
                desc = a.get("description", "")
                break

    text.delete("1.0", tk.END)

    if desc:
        text.insert(tk.END, desc)
    else:
        text.insert(tk.END, f"Editar comentario para: {name}")


tree.bind("<<TreeviewSelect>>", on_select)

# Aplicar tema inicial
aplicar_tema("oscuro")

root.mainloop()

driver.quit()
