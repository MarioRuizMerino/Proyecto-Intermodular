from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from getpass import getpass
import json
import requests
from bs4 import BeautifulSoup
import os

# === CONFIG ===
MOODLE_URL = "https://educacionadistancia.juntadeandalucia.es/centros/malaga/login/index.php"
MOODLE_BASE = "https://educacionadistancia.juntadeandalucia.es/centros/malaga"
username = os.environ.get("USERNAME")
COOKIES_PATH = fr"C:\Users\{username}\Desktop\moodle_cookies.json"

USERNAME = input("Pon tu usuario: ")
PASSWORD = getpass("Pon tu contraseña: ")

# === SETUP SELENIUM ===
chrome_options = Options()

# Descomentar si quieres que no se vea el navegador
# chrome_options.add_argument("--headless=new")
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

# Step 1: Open Moodle login page
driver.get(MOODLE_URL)

# Step 2: Click CAS login button (Acceso Único Educación)
cas_button = driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
cas_button.click()

# Step 3: Fill in CAS username and password
driver.find_element(By.ID, "username").send_keys(USERNAME)
driver.find_element(By.ID, "password").send_keys(PASSWORD)

# Step 4: Submit the form
driver.find_element(By.NAME, "submit").click()

print("Ya casi estás!")

# ======= EXTRAER Y GUARDAR COOKIES =======
cookies = driver.get_cookies()

with open(COOKIES_PATH, "w", encoding="utf-8") as f:
    json.dump(cookies, f, indent=4, ensure_ascii=False)

print(f"Cookies guardadas en: {COOKIES_PATH}")

driver.quit()

# ======= USAR COOKIES CON REQUESTS =======
with open(COOKIES_PATH, "r", encoding="utf-8") as f:
    selenium_cookies = json.load(f)

session = requests.Session()
for c in selenium_cookies:
    # incluir dominio y path mejora que las acepte bien
    session.cookies.set(
        c["name"],
        c["value"],
        domain=c.get("domain"),
        path=c.get("path")
    )

# Área personal (para luego sacar cursos del HTML)
def get_home_html():
    url = f"{MOODLE_BASE}/my/"
    r = session.get(url)
    print("URL devuelta por /my/:", r.url)  # para comprobar si redirige al login
    return r.text

html_home = get_home_html()
print(html_home[:1000])

# Descargar deberes
def get_assignments(courseid):
    url = f"{MOODLE_BASE}/mod/assign/index.php?id={courseid}"
    r = session.get(url)
    return r.text  # HTML con los enlaces a tareas


def parse_courses(html):
    soup = BeautifulSoup(html, "html.parser")
    courses = []
    # Ajusta los selectores a cómo se ve tu Moodle.
    # Suele haber bloques de cursos con enlaces a /course/view.php?id=XXX
    for a in soup.select('a[href*="/course/view.php?id="]'):
        name = a.get_text(strip=True)
        href = a["href"]
        courses.append({"name": name, "url": href})
    return courses

courses = parse_courses(html_home)
print("Cursos encontrados:")
for c in courses:
    print("-", c["name"], "->", c["url"])

def get_assignments_html(course_url):
    r = session.get(course_url)
    return r.text

def parse_assignments(html):
    soup = BeautifulSoup(html, "html.parser")
    assignments = []
    # En muchos Moodles, las tareas son enlaces a /mod/assign/view.php
    for a in soup.select('a[href*="/mod/assign/view.php?id="]'):
        name = a.get_text(strip=True)
        href = a["href"]
        assignments.append({"name": name, "url": href})
    return assignments


import tkinter as tk
from tkinter import ttk

# Construir estructura: cursos + tareas
for c in courses:
    html_course = get_assignments_html(c["url"])
    c["assignments"] = parse_assignments(html_course)

# ==== INTERFAZ ====
root = tk.Tk()
root.title("Cursos y tareas - Moodle")

tree = ttk.Treeview(root)
tree["columns"] = ("tipo",)
tree.column("#0", width=300)
tree.column("tipo", width=100)
tree.heading("#0", text="Nombre")
tree.heading("tipo", text="Tipo")

# Insertar cursos y tareas
for i, c in enumerate(courses):
    cid = tree.insert("", "end", text=c["name"], values=("Curso",))
    for a in c.get("assignments", []):
        tree.insert(cid, "end", text=a["name"], values=("Tarea",))

tree.pack(fill="both", expand=True)

# Campo modificable (ejemplo: notas o comentarios)
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

root.mainloop()
