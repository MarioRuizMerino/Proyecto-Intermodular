import os
import json
import threading
import webbrowser
from urllib.parse import urlparse, parse_qs

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
class MoodleApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.driver = None
        self.courses = []
        self.provincia_nombre = ""
        self.moodle_base = ""
        self.moodle_login_url = ""
        
        self.title("Moodle Suite — Gestión Inteligente")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.crear_sidebar()
        
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.courses_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.progress_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        self.actual_frame = "home"
        self.show_frame("home")

    def crear_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=160, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="📚 MOODLE\nPRO", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Inicio",
                                       fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                       anchor="w", command=self.home_button_event)
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.courses_button = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Mis Cursos",
                                          fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                          anchor="w", command=self.courses_button_event)
        self.courses_button.grid(row=2, column=0, sticky="ew")

        self.progress_button = ctk.CTkButton(self.sidebar_frame, corner_radius=0, height=40, border_spacing=10, text="Progreso",
                                           fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                           anchor="w", command=self.progress_button_event)
        self.progress_button.grid(row=3, column=0, sticky="ew")

        self.appearance_mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                    command=lambda new_mode: ctk.set_appearance_mode(new_mode))
        self.appearance_mode_menu.grid(row=5, column=0, padx=20, pady=20, sticky="s")

    def show_frame(self, name):
        self.home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
        self.courses_button.configure(fg_color=("gray75", "gray25") if name == "courses" else "transparent")
        self.progress_button.configure(fg_color=("gray75", "gray25") if name == "progress" else "transparent")

        self.home_frame.grid_forget()
        self.courses_frame.grid_forget()
        self.progress_frame.grid_forget()

        if name == "home": self.home_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        if name == "courses": self.courses_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        if name == "progress": self.progress_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    def home_button_event(self): self.show_frame("home")
    def courses_button_event(self): self.show_frame("courses")
    def progress_button_event(self): 
        self.actualizar_vista_progreso()
        self.show_frame("progress")

    # ------------------ MANEJO DE COOKIES ------------------
    def cargar_cookies(self):
        """Carga las cookies del JSON si existe."""
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, "r") as f:
                return json.load(f)
        return None

    def guardar_cookies(self):
        """Guarda las cookies actuales de la sesión en un JSON."""
        cookies = self.driver.get_cookies()
        with open(COOKIES_FILE, "w") as f:
            json.dump(cookies, f)

    # ------------------ LÓGICA DE NEGOCIO ------------------
    def login_y_scraping_async(self, user, password):
        # 1. Bloquear UI para evitar dobles clics
        self.login_btn.configure(state="disabled", text="Conectando...")
        self.status_label.configure(text="Iniciando navegador...", text_color="yellow")

        def tarea():
            try:
                opts = Options()
                opts.add_argument("--headless=new")
                self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
                
                # 2. Intentar logueo con Cookies primero
                cookies = self.cargar_cookies()
                sesion_valida = False

                if cookies:
                    self.after(0, lambda: self.status_label.configure(text="Probando sesión guardada..."))
                    # Obligatorio visitar el dominio antes de inyectar cookies
                    self.driver.get(self.moodle_base) 
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)
                    
                    self.driver.get(f"{self.moodle_base}/my/")
                    # Si no nos redirige al login, la sesión sigue viva
                    if "login" not in self.driver.current_url:
                        sesion_valida = True

                # 3. Si no hay cookies o caducaron, login manual
                if not sesion_valida:
                    self.after(0, lambda: self.status_label.configure(text="Iniciando sesión con credenciales..."))
                    self.driver.get(self.moodle_login_url)
                    
                    try: 
                        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn-primary"))).click()
                    except TimeoutException: 
                        pass # Si no hay botón previo, continuamos
                    
                    self.driver.find_element(By.ID, "username").send_keys(user)
                    self.driver.find_element(By.ID, "password").send_keys(password)
                    self.driver.find_element(By.NAME, "submit").click()

                    # 4. CONTROL DE ERRORES DE LOGIN (CAS Junta Andalucía)
                    try:
                        # Comprobamos si aparece un mensaje de error genérico del CAS
                        error_msg = self.driver.find_element(By.CSS_SELECTOR, ".alert-danger").text
                        self.after(0, lambda: self.error_login(f"Credenciales incorrectas: {error_msg}"))
                        return # Salimos del hilo
                    except NoSuchElementException:
                        pass # No hay error, seguimos

                    # Comprobar si hemos llegado al dashboard
                    WebDriverWait(self.driver, 10).until(EC.url_contains("/my/"))
                    self.guardar_cookies() # Login exitoso, guardamos sesión

                # 5. Extracción de datos (Scraping)
                self.after(0, lambda: self.status_label.configure(text="Extrayendo cursos y tareas..."))
                self.driver.get(f"{self.moodle_base}/my/")
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                self.courses = []
                
                for a in soup.select('a[href*="/course/view.php?id="]'):
                    name = a.get_text(strip=True)
                    if name and name not in [c['name'] for c in self.courses]:
                        self.courses.append({"name": name, "url": a["href"], "assignments": []})
                
                for i, curso in enumerate(self.courses[:5]):
                    cid = parse_qs(urlparse(curso["url"]).query).get("id", [None])[0]
                    self.driver.get(f"{self.moodle_base}/mod/assign/index.php?id={cid}")
                    s = BeautifulSoup(self.driver.page_source, "html.parser")
                    for row in s.select("table.generaltable tbody tr"):
                        link = row.select_one("a")
                        if link:
                            cols = row.find_all("td")
                            curso["assignments"].append({
                                "name": link.get_text(strip=True),
                                "url": link["href"],
                                "due_date": cols[2].get_text(strip=True) if len(cols) > 2 else "N/A"
                            })
                
                self.after(0, self.finalizar_carga)

            except TimeoutException:
                self.after(0, lambda: self.error_login("Tiempo de espera agotado. Moodle podría estar caído."))
            except Exception as e:
                self.after(0, lambda: self.error_login(f"Error inesperado: {str(e)}"))
            finally:
                if self.driver:
                    self.driver.quit()

        threading.Thread(target=tarea, daemon=True).start()

    def error_login(self, mensaje):
        """Maneja fallos de login restaurando la UI."""
        messagebox.showerror("Error de Acceso", mensaje)
        self.status_label.configure(text="Esperando conexión...", text_color="gray")
        self.login_btn.configure(state="normal", text="Sincronizar Moodle")
        # Limpiamos solo la contraseña por comodidad
        self.p_ent.delete(0, 'end')

    def finalizar_carga(self):
        """Actualiza la interfaz con los datos obtenidos."""
        self.status_label.configure(text="¡Sincronización completada!", text_color="green")
        self.login_btn.configure(state="normal", text="Sincronizar Moodle")

        for widget in self.courses_frame.winfo_children(): widget.destroy()
        
        for curso in self.courses:
            f = ctk.CTkFrame(self.courses_frame)
            f.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(f, text=curso['name'], font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
            for t in curso['assignments']:
                btn = ctk.CTkButton(f, text=f"📝 {t['name']} - {t['due_date']}", 
                                   fg_color="transparent", anchor="w", 
                                   command=lambda u=t['url']: webbrowser.open(u))
                btn.pack(fill="x", padx=20)
        
        self.show_frame("courses")

    def actualizar_vista_progreso(self):
        for widget in self.progress_frame.winfo_children(): widget.destroy()
        total_tareas = sum(len(c["assignments"]) for c in self.courses)
        
        ctk.CTkLabel(self.progress_frame, text="Análisis de Rendimiento", font=("Arial", 22, "bold")).pack(pady=20)
        f = ctk.CTkFrame(self.progress_frame)
        f.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(f, text=f"Tareas detectadas: {total_tareas}", font=("Arial", 16)).pack(pady=10)
        
        prog = ctk.CTkProgressBar(f)
        prog.pack(pady=10, padx=20, fill="x")
        prog.set(min(1.0, total_tareas / 20))

# ===================== EJECUCIÓN =====================
if __name__ == "__main__":
    app = MoodleApp()
    app.moodle_login_url, app.moodle_base = construir_urls("malaga") 
    
    ctk.CTkLabel(app.home_frame, text="Panel de Acceso", font=("Arial", 24, "bold")).pack(pady=30)
    
    # He convertido los Entry en atributos de clase (self.u_ent) para poder limpiarlos desde error_login()
    app.u_ent = ctk.CTkEntry(app.home_frame, placeholder_text="Usuario IDEA", width=300)
    app.u_ent.pack(pady=10)
    app.p_ent = ctk.CTkEntry(app.home_frame, placeholder_text="Contraseña", show="*", width=300)
    app.p_ent.pack(pady=10)
    
    app.status_label = ctk.CTkLabel(app.home_frame, text="Esperando conexión...", text_color="gray")
    app.status_label.pack(pady=5)

    def log_btn():
        # Verificación rápida antes de mandar al hilo
        if not app.u_ent.get() or not app.p_ent.get():
            messagebox.showwarning("Atención", "Por favor, rellena usuario y contraseña.")
            return
        app.login_y_scraping_async(app.u_ent.get(), app.p_ent.get())
        
    app.login_btn = ctk.CTkButton(app.home_frame, text="Sincronizar Moodle", command=log_btn, height=45, width=200)
    app.login_btn.pack(pady=20)
    
    app.mainloop()
