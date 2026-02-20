import os
import json
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ======== CONFIGURACIÓN Y CONSTANTES ========
PROVINCIAS = {
    "Almería": "almeria", "Cádiz": "cadiz", "Córdoba": "cordoba", 
    "Granada": "granada", "Huelva": "huelva", "Jaén": "jaen", 
    "Málaga": "malaga", "Sevilla": "sevilla"
}

COOKIES_FILE = os.path.join(os.path.expanduser("~"), "moodle_cookies.json")

def construir_urls(slug_provincia):
    base = f"https://educacionadistancia.juntadeandalucia.es/centros/{slug_provincia}"
    return f"{base}/login/index.php", base

# ===================== CLASE PRINCIPAL DE LA APP =====================
class MoodleApp:
    def __init__(self):
        self.driver = None
        self.courses = []
        self.provincia_nombre = ""
        self.moodle_base = ""
        self.moodle_login_url = ""
        
        # Configuración estética global
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    def iniciar(self):
        """Punto de entrada de la aplicación."""
        self.provincia_nombre = self.gui_seleccionar_provincia()
        if not self.provincia_nombre: return
        
        slug = PROVINCIAS[self.provincia_nombre]
        self.moodle_login_url, self.moodle_base = construir_urls(slug)
        
        # Intentar login automático con cookies
        if not self.intentar_login_cookies():
            # Si fallan las cookies, pedir credenciales
            user, password = self.gui_pedir_credenciales()
            if user and password:
                self.login_completo(user, password)
            else:
                return

    # ------------------ LÓGICA DE SELENIUM ------------------
    def configurar_driver(self, headless=True):
        opts = Options()
        if headless: opts.add_argument("--headless=new")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

    def intentar_login_cookies(self):
        """Verifica si hay una sesión guardada válida."""
        if not os.path.exists(COOKIES_FILE): return False
        
        self.configurar_driver(headless=True)
        try:
            self.driver.get(self.moodle_base)
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            
            self.driver.get(f"{self.moodle_base}/my/")
            # Si estamos en /my/ y no en /login/, la sesión es válida
            if "login" not in self.driver.current_url:
                self.extraer_datos_y_lanzar()
                return True
        except:
            pass
        return False

    def login_completo(self, user, password):
        """Proceso de login CAS y extracción de datos."""
        carga, actualizar = self.gui_pantalla_carga("Iniciando sesión segura...")
        
        try:
            if not self.driver: self.configurar_driver(headless=True)
            self.driver.get(self.moodle_login_url)
            
            # Click en botón Identifícate (CAS) si existe
            try:
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-primary"))).click()
            except: pass

            actualizar("Autenticando en la Junta...", "Enviando credenciales...")
            self.driver.find_element(By.ID, "username").send_keys(user)
            self.driver.find_element(By.ID, "password").send_keys(password)
            self.driver.find_element(By.NAME, "submit").click()

            # Guardar nuevas cookies
            with open(COOKIES_FILE, "w") as f:
                json.dump(self.driver.get_cookies(), f)

            self.extraer_datos_y_lanzar(actualizar)
            carga.destroy()
        except Exception as e:
            carga.destroy()
            messagebox.showerror("Error de Login", f"No se pudo iniciar sesión: {str(e)}")

    def extraer_datos_y_lanzar(self, callback_msg=None):
        """Extrae cursos y tareas y lanza el Dashboard."""
        if callback_msg: callback_msg("Obteniendo cursos...", "Escaneando Moodle...")
        
        self.driver.get(f"{self.moodle_base}/my/")
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        
        # Parseo de cursos
        self.courses = []
        seen = set()
        for a in soup.select('a[href*="/course/view.php?id="]'):
            name = a.get_text(strip=True)
            url = a["href"]
            if url not in seen and name:
                seen.add(url)
                self.courses.append({"name": name, "url": url, "assignments": []})

        # Parseo de tareas por curso
        for i, curso in enumerate(self.courses, 1):
            if callback_msg: callback_msg(f"Procesando curso {i}/{len(self.courses)}", curso['name'][:40])
            curso["assignments"] = self.get_assignments(curso["url"])

        self.gui_lanzar_dashboard()

    def get_assignments(self, course_url):
        cid = parse_qs(urlparse(course_url).query).get("id", [None])[0]
        if not cid: return []
        self.driver.get(f"{self.moodle_base}/mod/assign/index.php?id={cid}")
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        
        tasks = []
        for row in soup.select("table.generaltable tbody tr"):
            link = row.select_one("a")
            if link:
                cols = row.find_all("td")
                tasks.append({
                    "name": link.get_text(strip=True),
                    "url": link["href"],
                    "due_date": cols[2].get_text(strip=True) if len(cols) > 2 else "Sin fecha"
                })
        return tasks

    # ------------------ INTERFACES GRÁFICAS (GUI) ------------------

    def gui_seleccionar_provincia(self):
        ventana = ctk.CTk()
        ventana.title("Moodle — Inicio")
        ventana.geometry("360x300")
        res = {"val": None}

        ctk.CTkLabel(ventana, text="📚 Moodle Pro", font=("Arial", 22, "bold")).pack(pady=20)
        combo = ctk.CTkOptionMenu(ventana, values=list(PROVINCIAS.keys()), width=200)
        combo.pack(pady=10)

        def ok():
            res["val"] = combo.get()
            ventana.destroy()
        
        ctk.CTkButton(ventana, text="Siguiente", command=ok).pack(pady=20)
        ventana.mainloop()
        return res["val"]

    def gui_pedir_credenciales(self):
        ventana = ctk.CTk()
        ventana.title("Login Junta")
        ventana.geometry("400x400")
        res = {"u": None, "p": None}

        ctk.CTkLabel(ventana, text="Credenciales IDEA", font=("Arial", 18, "bold")).pack(pady=20)
        u_entry = ctk.CTkEntry(ventana, placeholder_text="Usuario", width=250)
        u_entry.pack(pady=10)
        p_entry = ctk.CTkEntry(ventana, placeholder_text="Contraseña", show="*", width=250)
        p_entry.pack(pady=10)

        def login():
            res["u"], res["p"] = u_entry.get(), p_entry.get()
            ventana.destroy()

        ctk.CTkButton(ventana, text="Entrar", command=login).pack(pady=20)
        ventana.mainloop()
        return res["u"], res["p"]

    def gui_pantalla_carga(self, msg_inicial):
        ventana = ctk.CTk()
        ventana.geometry("300x150")
        lbl = ctk.CTkLabel(ventana, text=msg_inicial)
        lbl.pack(pady=20)
        bar = ctk.CTkProgressBar(ventana)
        bar.pack(padx=20, fill="x")
        bar.start()
        
        def actualizar(m1, m2=""):
            lbl.configure(text=f"{m1}\n{m2}")
            ventana.update()
        
        return ventana, actualizar

    def gui_lanzar_dashboard(self):
        # Aquí va vuestra interfaz del Dashboard (puedes reutilizar la que tenías)
        # Por brevedad, he simplificado el lanzamiento
        app = ctk.CTk()
        app.title(f"Dashboard - {self.provincia_nombre}")
        app.geometry("1000x600")
        
        # Sidebar
        sidebar = ctk.CTkFrame(app, width=200)
        sidebar.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(sidebar, text="MENU", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Main Content
        main_frame = ctk.CTkScrollableFrame(app)
        main_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        # Poblar con cursos
        for curso in self.courses:
            c_frame = ctk.CTkFrame(main_frame)
            c_frame.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(c_frame, text=curso['name'], font=("Arial", 13, "bold")).pack(anchor="w", padx=10)
            for task in curso['assignments']:
                t_btn = ctk.CTkButton(c_frame, text=f"📝 {task['name']} ({task['due_date']})", 
                                     fg_color="transparent", anchor="w",
                                     command=lambda u=task['url']: webbrowser.open(u))
                t_btn.pack(fill="x", padx=20)

        app.mainloop()

if __name__ == "__main__":
    app = MoodleApp()
    app.iniciar()