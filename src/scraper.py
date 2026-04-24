from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import json
import os

class LoginFallidoError(Exception):
    """Se lanza cuando las credenciales son incorrectas."""
    pass

class MoodleScraper:
    def __init__(self, moodle_url, moodle_base):
        self.moodle_url = moodle_url
        self.moodle_base = moodle_base
        self.driver = self._init_driver()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")   # navegador invisible
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Detectar automáticamente el binario disponible (Chrome o Chromium)
        binarios = [
            # Linux — instalación nativa
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            # Linux — Flatpak (enlace estable independiente de versión)
            "/var/lib/flatpak/app/com.google.Chrome/current/active/files/extra/google-chrome",
            # Windows
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for b in binarios:
            if os.path.exists(b):
                chrome_options.binary_location = b
                break

        # Selenium Manager (Selenium 4.6+) descarga automáticamente
        # el ChromeDriver correcto para la versión del navegador instalada.
        return webdriver.Chrome(options=chrome_options)

    def login(self, username, password, actualizar_carga_fn=None):
        if actualizar_carga_fn:
            actualizar_carga_fn("Iniciando sesión en Moodle...", "Abriendo página de acceso...")

        self.driver.get(self.moodle_url)

        try:
            cas_button = self.driver.find_element(By.CSS_SELECTOR, "a.btn.btn-primary")
            cas_button.click()
        except Exception:
            pass

        if actualizar_carga_fn:
            actualizar_carga_fn("Iniciando sesión en Moodle...", "Introduciendo credenciales...")

        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.NAME, "submit").click()

        # Esperar a que cargue
        import time
        time.sleep(3)

        # Comprobar login fallido DESPUÉS de hacer submit
        url_actual = self.driver.current_url.lower()
        html = self.driver.page_source.lower()
        indicadores_error = [
            "credenciales incorrectas",
            "usuario o contraseña incorrect",
            "incorrect username or password",
            "identificación errónea",
            "authentication failed",
        ]
        es_fallo = any(txt in html for txt in indicadores_error)
        sigue_en_login = "/cas/login" in url_actual or (
                    "/login" in url_actual and self.moodle_base.lower() not in url_actual)

        if es_fallo or sigue_en_login:
            raise LoginFallidoError("Usuario o contraseña incorrectos.")

        print("Login correcto.")
    def guardar_cookies(self):
        cookies_path = os.path.join(os.path.expanduser("~"), "moodle_cookies.json")
        try:
            with open(cookies_path, "w", encoding="utf-8") as f:
                json.dump(self.driver.get_cookies(), f, indent=4, ensure_ascii=False)
            return cookies_path
        except Exception as e:
            print(f"No se pudieron guardar cookies: {e}")
            return None

    def get_course_id(self, url):
        qs = parse_qs(urlparse(url).query)
        return qs.get("id", [None])[0]

    def parse_courses(self, html):
        soup = BeautifulSoup(html, "html.parser")
        courses = []
        seen = set()
        for a in soup.select('a[href*="/course/view.php?id="]'):
            name = a.get_text(strip=True)
            href = a["href"]
            if href not in seen and name:
                seen.add(href)
                courses.append({"name": name, "url": href})
        return courses

    def get_assignment_details(self, assign_url):
        try:
            self.driver.get(assign_url)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")

            desc_div = soup.select_one("div.activity-description#intro")
            description = desc_div.get_text(separator="\n", strip=True) if desc_div else "Sin descripción."

            estado_entrega = ""
            estado_calific = ""
            tiempo_restante = ""
            nota = ""

            status_table = soup.select_one("div.submissionstatustable table.generaltable")
            if status_table:
                for row in status_table.select("tr"):
                    th = row.select_one("th.cell.c0")
                    td = row.select_one("td.cell.c1")
                    if not th or not td: continue
                    label = th.get_text(strip=True).lower()
                    value = td.get_text(strip=True)
                    if "estado de la entrega" in label: estado_entrega = value
                    elif "calificaci" in label: estado_calific = value
                    elif "tiempo restante" in label or "fecha límite" in label: tiempo_restante = value

            feedback_table = soup.select_one("div.feedback table.generaltable")
            if feedback_table:
                for row in feedback_table.select("tr"):
                    th = row.select_one("th.cell.c0")
                    td = row.select_one("td.cell.c1")
                    if th and td and "calificación" in th.get_text(strip=True).lower():
                        nota = td.get_text(separator=" ", strip=True).replace("\xa0", " ")
                        break
            return description, estado_entrega, estado_calific, tiempo_restante, nota
        except Exception as e:
            print(f"Error obteniendo detalles de tarea: {e}")
            return "Error al cargar.", "", "", "", ""

    def get_all_assignments_from_index(self, course_url):
        cid = self.get_course_id(course_url)
        if not cid: return []
        index_url = f"{self.moodle_base}/mod/assign/index.php?id={cid}"
        self.driver.get(index_url)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        assignments = []
        for row in soup.select("table.generaltable tbody tr"):
            link = row.select_one("a")
            if not link: continue
            name = link.get_text(strip=True)
            href = link["href"]
            cols = row.find_all("td")
            due_date = cols[2].get_text(strip=True) if len(cols) > 2 else ""
            
            description, estado_entrega, estado_calific, tiempo_restante, nota = \
                self.get_assignment_details(href)

            assignments.append({
                "name": name,
                "url": href,
                "description": description,
                "due_date": due_date,
                "estado_entrega": estado_entrega,
                "estado_calific": estado_calific,
                "tiempo_restante": tiempo_restante,
                "nota": nota,
            })
        return assignments

    def quit(self):
        if self.driver:
            self.driver.quit()
