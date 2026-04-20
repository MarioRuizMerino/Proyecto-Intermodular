from src.config import PROVINCIAS
from src.gui import seleccionar_provincia, pedir_credenciales, mostrar_cargando, lanzar_dashboard
from src.scraper import MoodleScraper, LoginFallidoError
from src.cache import guardar_cache, cargar_cache, guardar_usuario, cargar_usuario
import threading
import sys

def construir_urls(slug_provincia):
    base = f"https://educacionadistancia.juntadeandalucia.es/centros/{slug_provincia}"
    return f"{base}/login/index.php", base

def main():
    provincia_nombre = seleccionar_provincia()
    if provincia_nombre is None:
        sys.exit("No se seleccionó provincia.")

    slug = PROVINCIAS[provincia_nombre]
    moodle_url, moodle_base = construir_urls(slug)

    # Cargar usuario guardado y cache anterior
    usuario_guardado = cargar_usuario()
    provincia_cache, courses_cache = cargar_cache()
    hay_cache = courses_cache is not None

    # Pedir credenciales (con usuario prerrellenado si existe)
    username, password = pedir_credenciales(usuario_guardado=usuario_guardado)
    if not username or not password:
        sys.exit("No se introdujeron credenciales.")

    guardar_usuario(username)

    # Abrir Chrome y hacer login
    carga_win, actualizar_carga, cerrar_carga = mostrar_cargando("Iniciando sesión...")
    scraper = MoodleScraper(moodle_url, moodle_base)

    try:
        scraper.login(username, password, actualizar_carga)
    except LoginFallidoError:
        cerrar_carga()
        scraper.quit()
        # Volver a mostrar login con error
        username, password = pedir_credenciales(error=True, usuario_guardado=username)
        sys.exit("Login fallido.")
    except Exception as e:
        cerrar_carga()
        scraper.quit()
        sys.exit(f"Error: {e}")

    cerrar_carga()

    # Contenedor para pasar datos entre hilos
    resultado = {"courses": None, "error": None}

    def cargar_en_segundo_plano():
        try:
            scraper.driver.get(f"{moodle_base}/my/")
            courses_nuevos = scraper.parse_courses(scraper.driver.page_source)
            for i, c in enumerate(courses_nuevos, 1):
                c["assignments"] = scraper.get_all_assignments_from_index(c["url"])

            # Marcar tareas nuevas respecto al cache
            if hay_cache:
                urls_viejas = {
                    a["url"]
                    for c_old in courses_cache
                    for a in c_old.get("assignments", [])
                }
                for c in courses_nuevos:
                    for a in c["assignments"]:
                        a["es_nuevo"] = a["url"] not in urls_viejas
            else:
                for c in courses_nuevos:
                    for a in c["assignments"]:
                        a["es_nuevo"] = False

            resultado["courses"] = courses_nuevos
            guardar_cache(provincia_nombre, courses_nuevos)
            print("[CACHE] Datos nuevos guardados.")
        except Exception as e:
            resultado["error"] = str(e)
            print(f"[SEGUNDO PLANO] Error: {e}")

    hilo = threading.Thread(target=cargar_en_segundo_plano, daemon=True)
    hilo.start()

    if hay_cache:
        # Marcar todo como no-nuevo en el cache mientras carga
        for c in courses_cache:
            for a in c.get("assignments", []):
                a["es_nuevo"] = False
        lanzar_dashboard(courses_cache, provincia_nombre, scraper.quit, resultado=resultado)
    else:
        # Primera vez: esperar a que cargue todo antes de abrir el dashboard
        carga_win, actualizar_carga, cerrar_carga = mostrar_cargando("Cargando tus datos...")
        hilo.join()
        cerrar_carga()
        if resultado["error"]:
            sys.exit(f"Error cargando datos: {resultado['error']}")
        lanzar_dashboard(resultado["courses"], provincia_nombre, scraper.quit, resultado=None)

if __name__ == "__main__":
    main()