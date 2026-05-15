from src.config import PROVINCIAS
from src.gui import seleccionar_provincia, pedir_credenciales, mostrar_cargando, lanzar_dashboard
from src.scraper import MoodleScraper, LoginFallidoError
from src.cache import guardar_cache, cargar_cache, guardar_usuario, cargar_usuario
import threading
import queue
import sys


def construir_urls(slug_provincia):
    base = f"https://educacionadistancia.juntadeandalucia.es/centros/{slug_provincia}"
    return f"{base}/login/index.php", base


def main():
    # 1. Provincia
    provincia_nombre = seleccionar_provincia()
    if provincia_nombre is None:
        sys.exit("No se seleccionó provincia.")

    slug = PROVINCIAS[provincia_nombre]
    moodle_url, moodle_base = construir_urls(slug)

    # 2. Cargar usuario y caché guardados
    usuario_guardado = cargar_usuario()
    provincia_cache, courses_cache = cargar_cache()
    hay_cache = courses_cache is not None

    # 3. Pedir credenciales (usuario prerrellenado si existe)
    username, password = pedir_credenciales(usuario_guardado=usuario_guardado)
    if not username or not password:
        sys.exit("No se introdujeron credenciales.")
    guardar_usuario(username)

    # 4. Login con ventana de carga + threading para no congelar la UI
    login_queue = queue.Queue()
    carga_win, cerrar_carga = mostrar_cargando("Iniciando sesión...", login_queue)

    scraper_holder = {"scraper": None}

    def login_thread():
        scraper = MoodleScraper(moodle_url, moodle_base)
        scraper_holder["scraper"] = scraper

        def upd(titulo, sub=""):
            login_queue.put(("update", titulo, sub))

        try:
            scraper.login(username, password, upd)
            login_queue.put(("ok",))
        except LoginFallidoError:
            scraper.quit()
            login_queue.put(("login_error",))
        except Exception as e:
            scraper.quit()
            login_queue.put(("error", str(e)))

    threading.Thread(target=login_thread, daemon=True).start()

    resultado = {"courses": None, "error": None, "progreso_queue": None}

    # 6. Cargar datos en segundo plano tras login OK
    def arrancar_carga_datos():
        scraper = scraper_holder["scraper"]

        def cargar_en_segundo_plano(progreso_queue):
            try:
                scraper.driver.get(f"{moodle_base}/my/")
                courses_nuevos = scraper.parse_courses(scraper.driver.page_source)
                total = len(courses_nuevos)
                progreso_queue.put(("total", total))

                for i, c in enumerate(courses_nuevos, 1):
                    progreso_queue.put(("curso", i, total, c["name"]))
                    c["assignments"] = scraper.get_all_assignments_from_index(c["url"])
                    progreso_queue.put(("curso_listo", i, c))

                # Marcar tareas nuevas respecto a la caché
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
                progreso_queue.put(("done",))

            except Exception as e:
                resultado["error"] = str(e)
                print(f"[SEGUNDO PLANO] Error: {e}")
                progreso_queue.put(("error", str(e)))

        if hay_cache:
            # Abrir dashboard con caché inmediatamente
            for c in courses_cache:
                for a in c.get("assignments", []):
                    a["es_nuevo"] = False

            progreso_queue = queue.Queue()
            resultado["progreso_queue"] = progreso_queue

            threading.Thread(
                target=cargar_en_segundo_plano,
                args=(progreso_queue,),
                daemon=True
            ).start()

            lanzar_dashboard(
                courses_cache,
                provincia_nombre,
                scraper.quit,
                progreso_queue=progreso_queue
            )

        else:
            # Sin caché: ventana de carga hasta tener todos los datos
            carga2_queue = queue.Queue()
            carga2_win, cerrar_carga2 = mostrar_cargando(
                "Cargando tus datos por primera vez...", carga2_queue
            )

            threading.Thread(
                target=cargar_en_segundo_plano,
                args=(carga2_queue,),
                daemon=True
            ).start()

            def poll_primera_carga():
                try:
                    while True:
                        msg = carga2_queue.get_nowait()
                        if msg[0] == "curso":
                            _, i, total, nombre = msg
                            carga2_win._actualizar(
                                f"Cargando tareas... ({i}/{total})",
                                nombre[:60]
                            )
                        elif msg[0] == "done":
                            cerrar_carga2()
                            lanzar_dashboard(
                                resultado["courses"],
                                provincia_nombre,
                                scraper.quit,
                                progreso_queue=None
                            )
                            return
                        elif msg[0] == "error":
                            cerrar_carga2()
                            sys.exit(f"Error cargando datos: {msg[1]}")
                except queue.Empty:
                    pass
                carga2_win.after(100, poll_primera_carga)

            carga2_win.after(100, poll_primera_carga)
            carga2_win.mainloop()

    # 5. Polling del login
    def poll_login():
        try:
            while True:
                msg = login_queue.get_nowait()
                kind = msg[0]

                if kind == "update":
                    carga_win._actualizar(msg[1], msg[2] if len(msg) > 2 else "")

                elif kind == "ok":
                    cerrar_carga()
                    arrancar_carga_datos()
                    return

                elif kind == "login_error":
                    cerrar_carga()
                    u, p = pedir_credenciales(error=True, usuario_guardado=username)
                    if not u or not p:
                        sys.exit("Login cancelado.")
                    guardar_usuario(u)
                    import os
                    os.execv(sys.executable, [sys.executable] + sys.argv)

                elif kind == "error":
                    cerrar_carga()
                    sys.exit(f"Error inesperado: {msg[1]}")

        except queue.Empty:
            pass
        carga_win.after(100, poll_login)

    carga_win.after(100, poll_login)
    carga_win.mainloop()


if __name__ == "__main__":
    main()