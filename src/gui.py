import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import webbrowser
from src.config import PROVINCIAS

def seleccionar_provincia():
    ventana = ctk.CTk()
    ventana.title("Moodle — Selecciona provincia")
    ventana.geometry("360x260")
    ventana.resizable(False, False)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    ctk.CTkLabel(ventana, text="📚 Moodle Andalucía",
                 font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30, 5))
    ctk.CTkLabel(ventana, text="Selecciona tu provincia para continuar",
                 font=ctk.CTkFont(size=13), text_color="gray").pack(pady=(0, 20))

    provincia_var = ctk.StringVar(value=list(PROVINCIAS.keys())[0])
    combo = ctk.CTkOptionMenu(ventana, variable=provincia_var,
                               values=list(PROVINCIAS.keys()),
                               width=220, height=38,
                               font=ctk.CTkFont(size=13))
    combo.pack(pady=5)

    result = {"provincia": None}

    def confirmar():
        result["provincia"] = provincia_var.get()
        ventana.destroy()

    ctk.CTkButton(ventana, text="Continuar →", command=confirmar,
                  width=220, height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)

    ventana.mainloop()
    return result["provincia"]


def pedir_credenciales(error=False):
    ventana = ctk.CTk()
    ventana.title("Moodle — Iniciar sesión")
    ventana.geometry("400x500")
    ventana.resizable(False, False)
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    result = {"username": None, "password": None}

    frame = ctk.CTkFrame(ventana, corner_radius=20,
                         fg_color="#1a1a2e",
                         border_width=1, border_color="#2a2a5a")
    frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.92)

    ctk.CTkLabel(frame, text="📚", font=ctk.CTkFont(size=44)).pack(pady=(30, 4))
    ctk.CTkLabel(frame, text="Bienvenido a Moodle",
                 font=ctk.CTkFont(size=20, weight="bold")).pack()
    ctk.CTkLabel(frame, text="Introduce tus credenciales de la Junta de Andalucía",
                 font=ctk.CTkFont(size=11), text_color="gray",
                 wraplength=300, justify="center").pack(pady=(4, 16))

    # ── Mensaje de error (visible solo si error=True) ──
    error_label = ctk.CTkLabel(
        frame,
        text="⚠️  Usuario o contraseña incorrectos. Inténtalo de nuevo." if error else "",
        text_color="#ef5350",
        font=ctk.CTkFont(size=11),
        wraplength=300,
        justify="center"
    )
    error_label.pack(pady=(0, 8))

    ctk.CTkLabel(frame, text="Usuario", font=ctk.CTkFont(size=12),
                 anchor="w").pack(fill="x", padx=30)
    user_entry = ctk.CTkEntry(frame, placeholder_text="Tu usuario...",
                               width=300, height=40, corner_radius=8,
                               font=ctk.CTkFont(size=13))
    user_entry.pack(padx=30, pady=(2, 14))

    ctk.CTkLabel(frame, text="Contraseña", font=ctk.CTkFont(size=12),
                 anchor="w").pack(fill="x", padx=30)
    pass_entry = ctk.CTkEntry(frame, placeholder_text="Tu contraseña...",
                               width=300, height=40, corner_radius=8,
                               font=ctk.CTkFont(size=13), show="•")
    pass_entry.pack(padx=30, pady=(2, 6))

    mostrar_var = ctk.BooleanVar(value=False)
    def toggle_pass():
        pass_entry.configure(show="" if mostrar_var.get() else "•")
    ctk.CTkCheckBox(frame, text="Mostrar contraseña", variable=mostrar_var,
                    command=toggle_pass, font=ctk.CTkFont(size=11),
                    text_color="gray").pack(anchor="w", padx=32, pady=(0, 16))

    # ── Error de campos vacíos ──
    campos_label = ctk.CTkLabel(frame, text="", text_color="#ef5350",
                                 font=ctk.CTkFont(size=11))
    campos_label.pack()

    def confirmar(event=None):
        u = user_entry.get().strip()
        p = pass_entry.get()
        if not u or not p:
            campos_label.configure(text="⚠️  Por favor, rellena todos los campos.")
            return
        result["username"] = u
        result["password"] = p
        ventana.destroy()

    ventana.bind("<Return>", confirmar)

    ctk.CTkButton(frame, text="Iniciar sesión →",
                  command=confirmar,
                  width=300, height=42,
                  corner_radius=8,
                  font=ctk.CTkFont(size=14, weight="bold"),
                  fg_color="#1565c0", hover_color="#1976d2").pack(padx=30, pady=(8, 0))

    ventana.mainloop()
    return result["username"], result["password"]


def mostrar_cargando(mensaje="Cargando..."):
    ventana = ctk.CTk()
    ventana.title("Moodle — Cargando")
    ventana.geometry("380x220")
    ventana.resizable(False, False)
    ctk.set_appearance_mode("dark")

    frame = ctk.CTkFrame(ventana, corner_radius=20, fg_color="#1a1a2e")
    frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.88)

    ctk.CTkLabel(frame, text="⏳", font=ctk.CTkFont(size=36)).pack(pady=(25, 6))

    msg_label = ctk.CTkLabel(frame, text=mensaje,
                              font=ctk.CTkFont(size=13, weight="bold"),
                              wraplength=280, justify="center")
    msg_label.pack(pady=(0, 12))

    barra = ctk.CTkProgressBar(frame, mode="indeterminate",
                                height=10, corner_radius=5,
                                progress_color="#4fc3f7")
    barra.pack(fill="x", padx=30, pady=(0, 10))
    barra.start()

    sub_label = ctk.CTkLabel(frame, text="Por favor, espera...",
                              font=ctk.CTkFont(size=11), text_color="gray")
    sub_label.pack()

    def actualizar(nuevo_msg, nuevo_sub=""):
        msg_label.configure(text=nuevo_msg)
        if nuevo_sub:
            sub_label.configure(text=nuevo_sub)
        ventana.update()

    def cerrar():
        barra.stop()
        ventana.destroy()

    ventana.update()
    return ventana, actualizar, cerrar


def lanzar_dashboard(courses, provincia_nombre, driver_quit_fn):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Moodle Dashboard — Cursos y Tareas")
    app.geometry("1280x760")
    app.minsize(900, 600)

    tema_actual = {"modo": "dark"}

    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=1)

    # ========== SIDEBAR ==========
    sidebar = ctk.CTkFrame(app, width=260, corner_radius=0,
                           fg_color=("#1a1a2e", "#1a1a2e"))
    sidebar.grid(row=0, column=0, sticky="nsew")
    sidebar.grid_propagate(False)
    sidebar.grid_rowconfigure(5, weight=1)

    ctk.CTkLabel(sidebar, text="📚", font=ctk.CTkFont(size=40)).grid(
        row=0, column=0, pady=(30, 0), padx=20, sticky="w")
    ctk.CTkLabel(sidebar, text="Moodle",
                 font=ctk.CTkFont(size=26, weight="bold"),
                 text_color="#4fc3f7").grid(row=1, column=0, pady=(0, 4), padx=20, sticky="w")
    ctk.CTkLabel(sidebar, text=f"Junta de Andalucía · {provincia_nombre}",
                 font=ctk.CTkFont(size=11), text_color="gray").grid(
        row=2, column=0, pady=(0, 25), padx=20, sticky="w")

    sep = ctk.CTkFrame(sidebar, height=1, fg_color="#333355")
    sep.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 20))

    nav_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
    nav_frame.grid(row=4, column=0, sticky="ew", padx=10)

    nav_items = [
        ("🏠  Inicio", None),
        ("📖  Cursos", None),
        ("📝  Tareas", None),
        ("📊  Progreso", None),
        ("⚙️   Ajustes", None),
    ]

    nav_buttons = []
    def nav_click(idx):
        for i, btn in enumerate(nav_buttons):
            btn.configure(fg_color="#1e3a5f" if i == idx else "transparent",
                          text_color="white" if i == idx else "#aaaacc")

    for i, (label, cmd) in enumerate(nav_items):
        btn = ctk.CTkButton(nav_frame, text=label,
                            font=ctk.CTkFont(size=14),
                            height=42, anchor="w",
                            fg_color="transparent",
                            text_color="#aaaacc",
                            hover_color="#1e3a5f",
                            corner_radius=8,
                            command=lambda i=i: nav_click(i))
        btn.pack(fill="x", pady=3)
        nav_buttons.append(btn)

    nav_click(0)

    def toggle_tema():
        modo = tema_actual["modo"]
        nuevo = "light" if modo == "dark" else "dark"
        tema_actual["modo"] = nuevo
        ctk.set_appearance_mode(nuevo)
        tema_btn.configure(text="☀️  Modo Claro" if nuevo == "light" else "🌙  Modo Oscuro")

    tema_btn = ctk.CTkButton(sidebar, text="🌙  Modo Oscuro",
                              font=ctk.CTkFont(size=12),
                              height=36, fg_color="#2a2a4a",
                              hover_color="#3a3a6a",
                              corner_radius=8,
                              command=toggle_tema)
    tema_btn.grid(row=6, column=0, sticky="ew", padx=15, pady=(0, 20))

    # ========== CONTENIDO PRINCIPAL ==========
    main = ctk.CTkFrame(app, corner_radius=0, fg_color=("gray92", "#16213e"))
    main.grid(row=0, column=1, sticky="nsew")
    main.grid_rowconfigure(2, weight=1)
    main.grid_columnconfigure(0, weight=1)

    # --- Cabecera ---
    header = ctk.CTkFrame(main, fg_color=("gray85", "#0f3460"), corner_radius=0, height=60)
    header.grid(row=0, column=0, sticky="ew")
    header.grid_propagate(False)
    ctk.CTkLabel(header, text="Panel de Control",
                 font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=25, pady=15)

    search_var = tk.StringVar()
    search_entry = ctk.CTkEntry(header, placeholder_text="🔍 Buscar tarea...",
                                textvariable=search_var, width=220, height=34)
    search_entry.pack(side="right", padx=20, pady=12)

    # --- CARDS DE RESUMEN ---
    cards_frame = ctk.CTkFrame(main, fg_color="transparent")
    cards_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=15)
    cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    total_cursos = len(courses)
    total_tareas = sum(len(c.get("assignments", [])) for c in courses)

    def make_card(parent, col, icon, label, value, color):
        card = ctk.CTkFrame(parent, corner_radius=14,
                            fg_color=("white", "#1b2a4a"),
                            border_width=1, border_color=("gray80", "#2a3f6f"))
        card.grid(row=0, column=col, padx=8, sticky="nsew", ipady=6)
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=30)).pack(pady=(15, 2))
        ctk.CTkLabel(card, text=str(value),
                     font=ctk.CTkFont(size=32, weight="bold"),
                     text_color=color).pack()
        ctk.CTkLabel(card, text=label,
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 15))

    make_card(cards_frame, 0, "📚", "Cursos", total_cursos, "#4fc3f7")
    make_card(cards_frame, 1, "📝", "Tareas totales", total_tareas, "#81c784")
    make_card(cards_frame, 2, "✅", "Pendientes", total_tareas, "#ffb74d")

    prog_card = ctk.CTkFrame(cards_frame, corner_radius=14,
                              fg_color=("white", "#1b2a4a"),
                              border_width=1, border_color=("gray80", "#2a3f6f"))
    prog_card.grid(row=0, column=3, padx=8, sticky="nsew", ipady=6)
    ctk.CTkLabel(prog_card, text="📈", font=ctk.CTkFont(size=30)).pack(pady=(15, 2))
    ctk.CTkLabel(prog_card, text="Progreso",
                 font=ctk.CTkFont(size=12), text_color="gray").pack()
    prog_bar = ctk.CTkProgressBar(prog_card, height=14, corner_radius=7,
                                   progress_color="#4fc3f7")
    prog_bar.pack(fill="x", padx=20, pady=8)
    prog_val = min(1.0, total_tareas / 30) if total_tareas > 0 else 0
    prog_bar.set(prog_val)
    ctk.CTkLabel(prog_card, text=f"{int(prog_val*100)}%",
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color="#4fc3f7").pack(pady=(0, 15))

    # --- PANEL INFERIOR: Árbol + Detalle ---
    bottom = ctk.CTkFrame(main, fg_color="transparent")
    bottom.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
    bottom.grid_rowconfigure(0, weight=1)
    bottom.grid_columnconfigure(0, weight=3)
    bottom.grid_columnconfigure(1, weight=2)

    # === ÁRBOL DE CURSOS ===
    tree_frame = ctk.CTkFrame(bottom, corner_radius=14,
                               fg_color=("white", "#1b2a4a"),
                               border_width=1, border_color=("gray80", "#2a3f6f"))
    tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    tree_frame.grid_rowconfigure(1, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(tree_frame, text="📋  Cursos y Tareas",
                 font=ctk.CTkFont(size=15, weight="bold")).grid(
        row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 6))

    style = ttk.Style()
    style.theme_use("default")
    style.configure("Moodle.Treeview",
                    background="#1b2a4a",
                    foreground="#e0e0e0",
                    fieldbackground="#1b2a4a",
                    borderwidth=0,
                    rowheight=28,
                    font=("Segoe UI", 11))
    style.configure("Moodle.Treeview.Heading",
                    background="#0f3460",
                    foreground="#4fc3f7",
                    font=("Segoe UI", 11, "bold"),
                    relief="flat")
    style.map("Moodle.Treeview",
              background=[("selected", "#1e3a5f")],
              foreground=[("selected", "white")])

    tree = ttk.Treeview(tree_frame, style="Moodle.Treeview")
    tree["columns"] = ("Tipo", "Fecha")
    tree.column("#0", width=320, anchor="w")
    tree.column("Tipo", width=90, anchor="center")
    tree.column("Fecha", width=140, anchor="center")
    tree.heading("#0", text="Nombre", anchor="w")
    tree.heading("Tipo", text="Tipo", anchor="center")
    tree.heading("Fecha", text="Fecha entrega", anchor="center")

    sb = ctk.CTkScrollbar(tree_frame, command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 10))
    sb.grid(row=1, column=1, sticky="ns", pady=(0, 10), padx=(0, 5))

    task_lookup = {}

    def poblar_arbol(filtro=""):
        for item in tree.get_children():
            tree.delete(item)
        task_lookup.clear()
        for curso in courses:
            asgs = curso.get("assignments", [])
            if filtro:
                asgs = [a for a in asgs if filtro.lower() in a["name"].lower()]
            cid = tree.insert("", "end",
                              text=f"📚  {curso['name']}",
                              values=("Curso", ""),
                              open=True)
            for tarea in asgs:
                tid = tree.insert(cid, "end",
                                  text=f"   📝  {tarea['name']}",
                                  values=("Tarea", tarea.get("due_date", "")))
                task_lookup[tid] = tarea

    poblar_arbol()
    search_var.trace_add("write", lambda *args: poblar_arbol(search_var.get()))

    # === PANEL DETALLE ===
    detail_frame = ctk.CTkFrame(bottom, corner_radius=14,
                                 fg_color=("white", "#1b2a4a"),
                                 border_width=1, border_color=("gray80", "#2a3f6f"))
    detail_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
    detail_frame.grid_rowconfigure(3, weight=1)
    detail_frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(detail_frame, text="🔍  Detalle",
                 font=ctk.CTkFont(size=15, weight="bold")).grid(
        row=0, column=0, sticky="w", padx=15, pady=(12, 4))

    detail_name = ctk.CTkLabel(detail_frame, text="Selecciona un elemento",
                                font=ctk.CTkFont(size=13, weight="bold"),
                                text_color="#4fc3f7", wraplength=320, justify="left")
    detail_name.grid(row=1, column=0, sticky="w", padx=15, pady=(4, 2))

    detail_type = ctk.CTkLabel(detail_frame, text="",
                                font=ctk.CTkFont(size=11), text_color="gray")
    detail_type.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 8))

    ctk.CTkFrame(detail_frame, height=1, fg_color="#2a3f6f").grid(
        row=3, column=0, sticky="ew", padx=15, pady=4)

    ctk.CTkLabel(detail_frame, text="📋  Información de la tarea:",
                 font=ctk.CTkFont(size=12, weight="bold")).grid(
        row=4, column=0, sticky="w", padx=15, pady=(10, 4))

    notes_box = ctk.CTkTextbox(detail_frame, corner_radius=8,
                                fg_color=("gray95", "#0f3460"),
                                font=ctk.CTkFont(size=12))
    notes_box.grid(row=5, column=0, sticky="nsew", padx=15, pady=(0, 8))
    detail_frame.grid_rowconfigure(5, weight=1)

    open_btn = ctk.CTkButton(detail_frame, text="🌐  Abrir en Moodle",
                              height=36, corner_radius=8,
                              fg_color="#1e3a5f", hover_color="#2a4f7f",
                              font=ctk.CTkFont(size=12),
                              state="disabled",
                              command=lambda: None)
    open_btn.grid(row=6, column=0, sticky="ew", padx=15, pady=(0, 15))

    current_url = {"url": None}

    def on_tree_select(event):
        sel = tree.focus()
        if not sel: return
        item = tree.item(sel)
        name = item["text"].strip().lstrip("📚📝 ")
        tipo = item["values"][0] if item["values"] else ""
        detail_name.configure(text=name)
        detail_type.configure(text=f"Tipo: {tipo}")
        notes_box.delete("0.0", "end")

        if sel in task_lookup:
            tarea = task_lookup[sel]
            due = tarea.get("due_date", "")
            desc = tarea.get("description", "Sin descripción disponible.")
            estado_entrega = tarea.get("estado_entrega", "")
            estado_calific = tarea.get("estado_calific", "")
            tiempo_restante = tarea.get("tiempo_restante", "")
            nota = tarea.get("nota", "")

            lineas = []
            if due: lineas.append(f"📅  Fecha de entrega: {due}")
            if tiempo_restante: lineas.append(f"⏱️  Tiempo restante: {tiempo_restante}")
            lineas.append("")
            if estado_entrega:
                e_lower = estado_entrega.lower()
                emoji_e = "❌" if ("no" in e_lower or "todavía" in e_lower or "realizado" in e_lower) else ("✅" if "entregad" in e_lower else "📋")
                lineas.append(f"{emoji_e}  Estado de entrega: {estado_entrega}")
            if estado_calific:
                emoji_c = "⏳" if "sin calificar" in estado_calific.lower() else ("🎓" if "calificad" in estado_calific.lower() else "📊")
                lineas.append(f"{emoji_c}  Estado calificación: {estado_calific}")
            if nota: lineas.append(f"🏆  Nota: {nota}")
            lineas.append("\n" + "─" * 40 + "\n\n📄  Descripción:\n")
            for linea in desc.split("\n"): lineas.append(linea)
            notes_box.insert("0.0", "\n".join(lineas))

            url = tarea.get("url", "")
            current_url["url"] = url
            if url: open_btn.configure(state="normal", command=lambda u=url: webbrowser.open(u))
            else: open_btn.configure(state="disabled")
        else:
            notes_box.insert("0.0", f"📚  Curso: {name}\n\nSelecciona una tarea para ver su detalle.")
            open_btn.configure(state="disabled")

    tree.bind("<<TreeviewSelect>>", on_tree_select)
    app.protocol("WM_DELETE_WINDOW", lambda: (app.destroy(), driver_quit_fn()))
    app.mainloop()