from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from getpass import getpass
from bs4 import BeautifulSoup
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import json
import os
import webbrowser
import time

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
    ventana.geometry("300x150")
    ventana.resizable(False, False)

    tk.Label(ventana, text="Provincia:", font=("Segoe UI", 10)).pack(pady=10)

    provincia_var = tk.StringVar()
    combo = ttk.Combobox(ventana, textvariable=provincia_var, state="readonly", font=("Segoe UI", 10))
    combo["values"] = list(PROVINCIAS.keys())
    combo.current(0)
    combo.pack(padx=20, pady=5)

    def confirmar():
        ventana.selected_provincia = provincia_var.get()
        ventana.destroy()

    tk.Button(ventana, text="Aceptar", command=confirmar, font=("Segoe UI", 10)).pack(pady=10)

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
NOTES_PATH   = fr"C:\Users\{username}\moodle_notas.json"

# ======= MODO DE EJECUCIÓN (RÁPIDO / LENTO) =======
modo = ""
while modo not in ("r", "l"):
    modo = input("¿Cómo quieres que se ejecute? [r]ápido / [l]ento: ").strip().lower()

if modo == "r":
    SPEED_FACTOR = 0.2   # menos esperas
else:
    SPEED_FACTOR = 1.0   # más lento

print("Modo seleccionado:", "rápido" if modo == "r" else "lento")

# Pedir credenciales
USERNAME = input("Pon tu usuario: ")
PASSWORD = getpass("Pon tu contraseña: ")

# === SETUP SELENIUM ===
chrome_options = Options()
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

# ======= GUARDAR COOKIES =======
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
    for a in soup.select('a[href*="/mod/assign/view.php?id="]'):
        name = a.get_text(strip=True)
        href = a["href"]
        assignments.append({"name": name, "url": href})
    return assignments

for c in courses:
    html_course = get_assignments_html(c["url"])
    c["assignments"] = parse_assignments(html_course)
    # aquí se nota el modo rápido/lento
    time.sleep(0.2 * SPEED_FACTOR)

# ======= NOTAS (PERSISTENCIA) =======
notes_data = {}  # iid -> texto
if os.path.exists(NOTES_PATH):
    try:
        with open(NOTES_PATH, "r", encoding="utf-8") as f:
            notes_data = json.load(f)
    except Exception as e:
        print("No se pudieron cargar las notas:", e)
        notes_data = {}

# ======= INTERFAZ MODERNA CON CUSTOMTKINTER =======
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Moodle Dashboard - Cursos y Tareas")
app.geometry("1200x700")

# Layout principal: sidebar + contenido
app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# ---------- SIDEBAR ----------
sidebar = ctk.CTkFrame(app, width=250, corner_radius=0)
sidebar.grid(row=0, column=0, sticky="nsew")
sidebar.grid_rowconfigure(1, weight=1)

# Logo/Título
logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
logo_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(20, 10))
ctk.CTkLabel(logo_frame, text="📚 Moodle", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)

# Info usuario
user_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
user_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
ctk.CTkLabel(user_frame, text=f"👤 {provincia_nombre}", font=ctk.CTkFont(size=14)).pack()

# Botones navegación
nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
nav_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

ctk.CTkButton(nav_frame, text="🏠 Inicio", font=ctk.CTkFont(size=14), height=40).pack(fill="x", pady=5)
ctk.CTkButton(nav_frame, text="📖 Cursos", font=ctk.CTkFont(size=14), height=40).pack(fill="x", pady=5)
ctk.CTkButton(nav_frame, text="📊 Progreso", font=ctk.CTkFont(size=14), height=40).pack(fill="x", pady=5)
ctk.CTkButton(nav_frame, text="⚙️  Perfil", font=ctk.CTkFont(size=14), height=40).pack(fill="x", pady=5)

# ---------- CONTENIDO PRINCIPAL ----------
main_content = ctk.CTkFrame(app, corner_radius=0)
main_content.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
main_content.grid_rowconfigure(1, weight=1)
main_content.grid_columnconfigure(0, weight=1)

# Cards de resumen
cards_container = ctk.CTkFrame(main_content)
cards_container.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
cards_container.grid_columnconfigure((0, 1, 2), weight=1)
cards_container.grid_rowconfigure(0, weight=1)

# Card Cursos
card1 = ctk.CTkFrame(cards_container, height=100, corner_radius=15)
card1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
ctk.CTkLabel(card1, text="📚 CURSOS", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 0))
ctk.CTkLabel(card1, text=f"{len(courses)}", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(0, 15))

# Card Tareas
total_tareas = sum(len(c.get("assignments", [])) for c in courses)
card2 = ctk.CTkFrame(cards_container, height=100, corner_radius=15)
card2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
ctk.CTkLabel(card2, text="📝 TAREAS", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 0))
ctk.CTkLabel(card2, text=f"{total_tareas}", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(0, 15))

# Card Progreso
card3 = ctk.CTkFrame(cards_container, height=100, corner_radius=15)
card3.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
ctk.CTkLabel(card3, text="📈 PROGRESO", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 0))
progress_bar = ctk.CTkProgressBar(card3, height=20)
progress_bar.pack(pady=(5, 15), padx=20, fill="x")
progress_value = min(1.0, total_tareas / 20) if total_tareas > 0 else 0
progress_bar.set(progress_value)

# Lista principal de cursos y tareas
list_frame = ctk.CTkFrame(main_content)
list_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
list_frame.grid_rowconfigure(0, weight=1)
list_frame.grid_columnconfigure(0, weight=1)

# Estilo moderno para Treeview
style = ttk.Style()
style.theme_use('default')
style.configure(
    "Dark.Treeview",
    background="#2B2B2B",
    foreground="white",
    fieldbackground="#2B2B2B",
    borderwidth=0,
    rowheight=25
)
style.configure(
    "Dark.Treeview.Heading",
    background="#1f538d",
    foreground="white",
    font=('Segoe UI', 11, 'bold')
)

tree = ttk.Treeview(list_frame, style="Dark.Treeview")
tree["columns"] = ("Tipo", "Estado")
tree.column("#0", width=400, anchor="w")
tree.column("Tipo", width=100, anchor="center")
tree.column("Estado", width=100, anchor="center")

tree.heading("#0", text="Nombre", anchor="w")
tree.heading("Tipo", text="Tipo", anchor="center")
tree.heading("Estado", text="Estado", anchor="center")

# Scrollbar
scrollbar = ctk.CTkScrollbar(list_frame, command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

tree.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")

# Mapa id_item -> url
item_urls = {}

# Insertar datos
for curso in courses:
    curso_id = tree.insert(
        "",
        "end",
        text=f"📚 {curso['name']}",
        values=("Curso", "Activo")
    )
    item_urls[curso_id] = curso["url"]

    for tarea in curso.get("assignments", []):
        tarea_id = tree.insert(
            curso_id,
            "end",
            text=f"📝 {tarea['name']}",
            values=("Tarea", "Pendiente")
        )
        item_urls[tarea_id] = tarea["url"]

# Área de comentarios
comment_frame = ctk.CTkFrame(main_content)
comment_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
ctk.CTkLabel(
    comment_frame,
    text="💭 Notas / Comentarios:",
    font=ctk.CTkFont(size=14, weight="bold")
).pack(pady=(15, 5), anchor="w", padx=15)

notes_text = ctk.CTkTextbox(comment_frame, height=100)
notes_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

def save_current_notes():
    selection = tree.focus()
    if not selection:
        return
    contenido = notes_text.get("0.0", "end").strip()
    notes_data[selection] = contenido

def on_tree_select(event):
    # Guardar notas del item anterior
    save_current_notes()

    selection = tree.focus()
    if selection:
        item = tree.item(selection)
        name = item['text']
        notes_text.delete("0.0", "end")

        texto_guardado = notes_data.get(selection, "")
        if not texto_guardado:
            texto_guardado = f"Notas para: {name}\n\nEscribe aquí tus comentarios..."

        notes_text.insert("0.0", texto_guardado)

def on_tree_double_click(event):
    selection = tree.focus()
    if not selection:
        return
    url = item_urls.get(selection)
    if url:
        webbrowser.open(url)

tree.bind("<<TreeviewSelect>>", on_tree_select)
tree.bind("<Double-1>", on_tree_double_click)

def on_close():
    # guardar notas del item seleccionado
    save_current_notes()
    try:
        with open(NOTES_PATH, "w", encoding="utf-8") as f:
            json.dump(notes_data, f, indent=4, ensure_ascii=False)
        print(f"Notas guardadas en: {NOTES_PATH}")
    except Exception as e:
        print("Error guardando notas:", e)
    try:
        driver.quit()
    except Exception:
        pass
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_close)
app.mainloop()
