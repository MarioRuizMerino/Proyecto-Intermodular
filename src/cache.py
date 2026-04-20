import json
import os

CACHE_FILE = os.path.join(os.path.expanduser("~"), ".moodle_cache.json")


def guardar_cache(provincia, courses):
    try:
        existing = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing["provincia"] = provincia
        existing["courses"] = courses
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"[CACHE] Guardado en {CACHE_FILE}")
    except Exception as e:
        print(f"[CACHE] Error guardando: {e}")


def cargar_cache():
    if not os.path.exists(CACHE_FILE):
        return None, None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("provincia"), data.get("courses")
    except Exception:
        return None, None


def guardar_usuario(username):
    try:
        existing = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing["ultimo_usuario"] = username
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE] Error guardando usuario: {e}")


def cargar_usuario():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("ultimo_usuario")
    except Exception:
        return None