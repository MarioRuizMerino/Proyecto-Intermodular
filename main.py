from src.config import PROVINCIAS
from src.gui import seleccionar_provincia, pedir_credenciales, mostrar_cargando, lanzar_dashboard
from src.scraper import MoodleScraper, LoginFallidoError
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

    # 2. Bucle de credenciales con reintento en login fallido
    error_login = False
    scraper = None
    while True:
        username, password = pedir_credenciales(error=error_login)
        if not username or not password:
            sys.exit("No se introdujeron credenciales.")

        carga_win, actualizar_carga, cerrar_carga = mostrar_cargando("Iniciando navegador...")
        scraper = MoodleScraper(moodle_url, moodle_base)

        try:
            scraper.login(username, password, actualizar_carga)
            break  # ✅ Login correcto, salir del bucle

        except LoginFallidoError:
            cerrar_carga()
            scraper.quit()
            error_login = True
            continue

        except Exception as e:
            cerrar_carga()
            scraper.quit()
            sys.exit(f"Error inesperado durante el login: {e}")

    # 3. A partir de aquí el login fue correcto
    try:
        actualizar_carga("Guardando sesión...", "Almacenando cookies...")
        scraper.guardar_cookies()

        actualizar_carga("Obteniendo tus cursos...", "Cargando área personal de Moodle...")
        scraper.driver.get(f"{moodle_base}/my/")
        courses = scraper.parse_courses(scraper.driver.page_source)
        print(f"Cursos encontrados: {len(courses)}")

        for i, c in enumerate(courses, 1):
            actualizar_carga(
                f"Cargando tareas... ({i}/{len(courses)})",
                c["name"][:50]
            )
            c["assignments"] = scraper.get_all_assignments_from_index(c["url"])

        total = sum(len(c["assignments"]) for c in courses)
        print(f"Total tareas encontradas: {total}")

        cerrar_carga()
        lanzar_dashboard(courses, provincia_nombre, scraper.quit)

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        scraper.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()