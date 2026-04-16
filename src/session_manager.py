import requests
import pickle
import os

SESSION_FILE = "session.pkl"


def cargar_sesion():
    session = requests.Session()

    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "rb") as f:
            session.cookies.update(pickle.load(f))

    return session


def guardar_sesion(session):
    with open(SESSION_FILE, "wb") as f:
        pickle.dump(session.cookies, f)