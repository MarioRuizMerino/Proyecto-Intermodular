from src.config import PROVINCIAS
from src.gui import seleccionar_provincia, pedir_credenciales, mostrar_cargando, lanzar_dashboard
from src.scraper import MoodleScraper
import sys

def construir_urls(slug_provincia):
    base = f"https://educacionadistancia.juntadeandalucia.es/centros/{slug_provincia}"
    return (
        f"{base}/login/index.php",
        base
    )

def main():
    # 1. Seleccionar provincia
    provincia_nombre = seleccionar_provincia()
    if provincia_nombre is None:
        sys.exit("No se seleccionó provincia.")

    slug = PROVINCIAS[provincia_nombre]
    moodle_url, moodle_base = construir_urls(slug)
    print(f"Provincia: {provincia_nombre} → {moodle_base}")

    # 2. Credenciales
    username, password = pedir_credenciales()
    if not username or not password:
        sys.exit("No se introdujeron credenciales.")

    # 3. Pantalla de carga
    carga_win, actualizar_carga, cerrar_carga = mostrar_cargando("Iniciando navegador...")

    # 4. Iniciar Scraper
    scraper = MoodleScraper(moodle_url, moodle_base)

    try:
        # 5. Login
        scraper.login(username, password, actualizar_carga)

        # 6. Guardar cookies
        actualizar_carga("Guardando sesión...", "Almacenando cookies...")
        scraper.guardar_cookies()

        # 7. Parsear cursos
        actualizar_carga("Obteniendo tus cursos...", "Cargando área personal de Moodle...")
        scraper.driver.get(f"{moodle_base}/my/")
        courses = scraper.parse_courses(scraper.driver.page_source)
        print(f"Cursos encontrados: {len(courses)}")

        # 8. Obtener tareas por cada curso
        for i, c in enumerate(courses, 1):
            actualizar_carga(
                f"Cargando tareas... ({i}/{len(courses)})",
                c["name"][:50]
            )
            c["assignments"] = scraper.get_all_assignments_from_index(c["url"])

        total = sum(len(c["assignments"]) for c in courses)
        print(f"Total tareas encontradas: {total}")

        # 9. Cerrar pantalla de carga
        cerrar_carga()

        # 10. Lanzar dashboard
        lanzar_dashboard(courses, provincia_nombre, scraper.quit)

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        scraper.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()
