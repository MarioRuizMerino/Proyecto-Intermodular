from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from getpass import getpass

# === CONFIG ===
MOODLE_URL = "https://educacionadistancia.juntadeandalucia.es/centros/malaga/login/index.php"
USERNAME = input("Pon tu usuario: ")
PASSWORD = getpass("Pon tu contraseña: ")

# === SETUP SELENIUM ===
chrome_options = Options()

# Comentar estas líneas si se quiere ver lo que pasa detrás 
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

# ---- TEST SUCCESS ----
print("Ya casi estás!")



# FUNCIONA HASTA AQUI


# Extraer cookies
import json

# After successful login:
cookies = driver.get_cookies()

# Save cookies to a file for later use
with open(r"C:\Users\mruimer1712\Desktop\moodle_cookies.json", "w", encoding="utf-8") as f:
    json.dump(cookies, f, indent=4, ensure_ascii=False)
print("Cookies saved to moodle_cookies.json")
driver.quit()


# Use these cookies in requests
import requests

MOODLE_BASE = "https://educacionadistancia.juntadeandalucia.es/centros/malaga"

# Load cookies saved by Selenium
with open("moodle_cookies.json", "r") as f:
    selenium_cookies = json.load(f)

# Convert Selenium cookie format → Requests cookie jar
session = requests.Session()
for c in selenium_cookies:
    session.cookies.set(c['name'], c['value'])


# Acceder a la mooodle


# Área personal (para luego sacar cursos del HTML)
def get_home_html():
    url = f"{MOODLE_URL}/my/"
    r = session.get(url)
    return r.text

html_home = get_home_html()
print(html_home[:1000])

# Descargar deberes
def get_assignments(courseid):
    url = f"{MOODLE_BASE}/mod/assign/index.php?id={courseid}"
    r = session.get(url)
    return r.text  # HTML page with assignment links
