import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import webbrowser
from src.config import PROVINCIAS
from tkinter import PanedWindow
import traceback


def _ignorar_after_errors(exc, val, tb):
    """Suprime los errores 'invalid command name' que CustomTkinter genera
    al cerrar ventanas con callbacks de animación pendientes."""
    if "invalid command name" not in str(val):
        traceback.print_exception(exc, val, tb)

def seleccionar_provincia():
    ventana = ctk.CTk()
    ventana.title("Moodle — Selecciona provincia")
    ventana.geometry("360x260")
    ventana.resizable(False, False)
    ventana.report_callback_exception = _ignorar_after_errors
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


def pedir_credenciales(error=False, usuario_guardado=None):
    ventana = ctk.CTk()
    ventana.title("Moodle — Iniciar sesión")
    ventana.geometry("400x500")
    ventana.resizable(False, False)
    ventana.report_callback_exception = _ignorar_after_errors
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

    # Si hay usuario guardado, rellenarlo en gris
    if usuario_guardado:
        user_entry.insert(0, usuario_guardado)
        user_entry.configure(text_color="gray")

        def on_user_click(event):
            user_entry.configure(text_color="white")
        user_entry.bind("<FocusIn>", on_user_click)

    ctk.CTkLabel(frame, text="Contraseña", font=ctk.CTkFont(size=12),
                 anchor="w").pack(fill="x", padx=30)
    pass_entry = ctk.CTkEntry(frame, placeholder_text="Tu contraseña...",
                               width=300, height=40, corner_radius=8,
                               font=ctk.CTkFont(size=13), show="•")
    pass_entry.pack(padx=30, pady=(2, 6))

    # Si hay usuario guardado, poner foco directo en contraseña
    if usuario_guardado:
        ventana.after(100, pass_entry.focus)

    mostrar_var = ctk.BooleanVar(value=False)
    def toggle_pass():
        pass_entry.configure(show="" if mostrar_var.get() else "•")
    ctk.CTkCheckBox(frame, text="Mostrar contraseña", variable=mostrar_var,
                    command=toggle_pass, font=ctk.CTkFont(size=11),
                    text_color="gray").pack(anchor="w", padx=32, pady=(0, 16))

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
    ventana.report_callback_exception = _ignorar_after_errors
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


def lanzar_dashboard(courses, provincia_nombre, driver_quit_fn, resultado=None):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # courses es mutable: empezamos con cache y luego se reemplaza
    estado = {"courses": courses}

    app = ctk.CTk()
    app.title("Moodle Dashboard — Cursos y Tareas")
    app.geometry("1280x760")
    app.minsize(900, 600)
    app.report_callback_exception = _ignorar_after_errors

    tema_actual = {"modo": "dark"}

    def calcular_stats():
        """Devuelve (total, pendientes, entregadas) según estado_entrega real."""
        total = pendientes = entregadas = 0
        for c in estado["courses"]:
            for a in c.get("assignments", []):
                total += 1
                if "entregad" in a.get("estado_entrega", "").lower():
                    entregadas += 1
                else:
                    pendientes += 1
        return total, pendientes, entregadas

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

    nav_labels = [
        ("🏠  Inicio",   "Panel de Control"),
        ("📖  Cursos",   "Mis Cursos"),
        ("📝  Tareas",   "Todas las Tareas"),
        ("📊  Progreso", "Progreso por Curso"),
        ("⚙️   Ajustes", "Ajustes"),
    ]

    nav_buttons = []

    def mostrar_vista(idx):
        for v in vistas:
            v.grid_remove()
        vistas[idx].grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        header_title.configure(text=nav_labels[idx][1])
        if idx in (1, 3):   # Cursos y Progreso se regeneran al entrar
            refrescar_vista(idx)

    def nav_click(idx):
        for i, btn in enumerate(nav_buttons):
            btn.configure(fg_color="#1e3a5f" if i == idx else "transparent",
                          text_color="white" if i == idx else "#aaaacc")
        mostrar_vista(idx)

    for i, (label, _) in enumerate(nav_labels):
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
    header_title = ctk.CTkLabel(header, text="Panel de Control",
                               font=ctk.CTkFont(size=20, weight="bold"))
    header_title.pack(side="left", padx=25, pady=15)

    # Indicador de carga en segundo plano
    carga_label = ctk.CTkLabel(header, text="⏳ Actualizando datos...",
                                font=ctk.CTkFont(size=11), text_color="#ffb74d")
    carga_label.pack(side="left", padx=10, pady=15)
    # Solo mostrar si hay resultado (segunda vez o más)
    if resultado is None:
        carga_label.pack_forget()

    search_var = tk.StringVar()
    search_entry = ctk.CTkEntry(header, placeholder_text="🔍 Buscar tarea...",
                                textvariable=search_var, width=220, height=34)
    search_entry.pack(side="right", padx=20, pady=12)

    # --- CARDS DE RESUMEN ---
    cards_frame = ctk.CTkFrame(main, fg_color="transparent")
    cards_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=15)
    cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

    def make_card(parent, col, icon, label, value, color):
        card = ctk.CTkFrame(parent, corner_radius=14,
                            fg_color=("white", "#1b2a4a"),
                            border_width=1, border_color=("gray80", "#2a3f6f"))
        card.grid(row=0, column=col, padx=8, sticky="nsew", ipady=6)
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=30)).pack(pady=(15, 2))
        val_lbl = ctk.CTkLabel(card, text=str(value),
                               font=ctk.CTkFont(size=32, weight="bold"),
                               text_color=color)
        val_lbl.pack()
        ctk.CTkLabel(card, text=label,
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 15))
        return val_lbl

    total_tareas, pendientes, entregadas = calcular_stats()
    total_cursos = len(estado["courses"])

    lbl_cursos     = make_card(cards_frame, 0, "📚", "Cursos",         total_cursos, "#4fc3f7")
    lbl_total      = make_card(cards_frame, 1, "📝", "Tareas totales", total_tareas, "#81c784")
    lbl_pendientes = make_card(cards_frame, 2, "⏳", "Pendientes",     pendientes,   "#ffb74d")

    prog_card = ctk.CTkFrame(cards_frame, corner_radius=14,
                              fg_color=("white", "#1b2a4a"),
                              border_width=1, border_color=("gray80", "#2a3f6f"))
    prog_card.grid(row=0, column=3, padx=8, sticky="nsew", ipady=6)
    ctk.CTkLabel(prog_card, text="📈", font=ctk.CTkFont(size=30)).pack(pady=(15, 2))
    ctk.CTkLabel(prog_card, text="Progreso (entregadas)",
                 font=ctk.CTkFont(size=12), text_color="gray").pack()
    prog_bar = ctk.CTkProgressBar(prog_card, height=14, corner_radius=7,
                                   progress_color="#4fc3f7")
    prog_bar.pack(fill="x", padx=20, pady=8)
    prog_val = entregadas / total_tareas if total_tareas > 0 else 0
    prog_bar.set(prog_val)
    lbl_progreso = ctk.CTkLabel(prog_card, text=f"{int(prog_val * 100)}%",
                                font=ctk.CTkFont(size=18, weight="bold"),
                                text_color="#4fc3f7")
    lbl_progreso.pack(pady=(0, 15))

    def actualizar_cards():
        t, p, e = calcular_stats()
        c = len(estado["courses"])
        lbl_cursos.configure(text=str(c))
        lbl_total.configure(text=str(t))
        lbl_pendientes.configure(text=str(p))
        v = e / t if t > 0 else 0
        prog_bar.set(v)
        lbl_progreso.configure(text=f"{int(v * 100)}%")

    # ═══════════════════════════════════════════════════════════════════════════
    # VISTA 0 — INICIO: árbol de cursos + panel detalle
    # ═══════════════════════════════════════════════════════════════════════════
    vista_inicio = ctk.CTkFrame(main, fg_color="transparent")
    vista_inicio.grid_rowconfigure(0, weight=1)
    vista_inicio.grid_columnconfigure(0, weight=1)

    paned = PanedWindow(vista_inicio, orient="horizontal", sashwidth=6)
    paned.pack(fill="both", expand=True)

    # === ÁRBOL DE CURSOS ===
    tree_frame = ctk.CTkFrame(paned, corner_radius=14,
                              fg_color=("white", "#1b2a4a"),
                              border_width=1, border_color=("gray80", "#2a3f6f"))
    paned.add(tree_frame)
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

    # Tag para tareas nuevas (punto rojo)
    tree = ttk.Treeview(tree_frame, style="Moodle.Treeview")
    tree["columns"] = ("Tipo", "Fecha")
    tree.column("#0", width=320, anchor="w")
    tree.column("Tipo", width=90, anchor="center")
    tree.column("Fecha", width=140, anchor="center")
    tree.heading("#0", text="Nombre", anchor="w")
    tree.heading("Tipo", text="Tipo", anchor="center")
    tree.heading("Fecha", text="Fecha entrega", anchor="center")
    tree.tag_configure("nueva", foreground="#ff5252")  # rojo para tareas nuevas

    sb = ctk.CTkScrollbar(tree_frame, command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 10))
    sb.grid(row=1, column=1, sticky="ns", pady=(0, 10), padx=(0, 5))

    task_lookup = {}

    def poblar_arbol(filtro=""):
        for item in tree.get_children():
            tree.delete(item)
        task_lookup.clear()
        for curso in estado["courses"]:
            asgs = curso.get("assignments", [])
            if filtro:
                asgs = [a for a in asgs if filtro.lower() in a["name"].lower()]
            curso_tiene_nuevas = any(a.get("es_nuevo", False) for a in asgs)
            texto_curso = f"📚  {'🔴 ' if curso_tiene_nuevas else ''}{curso['name']}"
            cid = tree.insert("", "end",
                              text=texto_curso,
                              values=("Curso", ""),
                              open=True)
            for tarea in asgs:
                es_nueva = tarea.get("es_nuevo", False)
                texto_tarea = f"   📝  {'🔴 ' if es_nueva else ''}{tarea['name']}"
                tags = ("nueva",) if es_nueva else ()
                tid = tree.insert(cid, "end",
                                  text=texto_tarea,
                                  values=("Tarea", tarea.get("due_date", "")),
                                  tags=tags)
                task_lookup[tid] = tarea

    poblar_arbol()
    search_var.trace_add("write", lambda *args: poblar_arbol(search_var.get()))

    # === PANEL DETALLE ===
    detail_frame = ctk.CTkFrame(paned, corner_radius=14,
                                fg_color=("white", "#1b2a4a"),
                                border_width=1, border_color=("gray80", "#2a3f6f"))
    paned.add(detail_frame)
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
        name = item["text"].strip().lstrip("📚📝🔴 ")
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
            if url:
                open_btn.configure(state="normal", command=lambda u=url: webbrowser.open(u))
            else:
                open_btn.configure(state="disabled")
        else:
            notes_box.insert("0.0", f"📚  Curso: {name}\n\nSelecciona una tarea para ver su detalle.")
            open_btn.configure(state="disabled")

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    # ═══════════════════════════════════════════════════════════════════════════
    # VISTA 1 — CURSOS: cards con progreso por curso
    # ═══════════════════════════════════════════════════════════════════════════
    vista_cursos = ctk.CTkScrollableFrame(main, fg_color="transparent")
    vista_cursos.grid_columnconfigure((0, 1, 2), weight=1)

    def _poblar_cursos():
        for w in vista_cursos.winfo_children():
            w.destroy()
        for idx_c, curso in enumerate(estado["courses"]):
            asgs = curso.get("assignments", [])
            total_c = len(asgs)
            entregadas_c = sum(1 for a in asgs if "entregad" in a.get("estado_entrega", "").lower())
            prog_c = entregadas_c / total_c if total_c > 0 else 0
            card = ctk.CTkFrame(vista_cursos, corner_radius=12,
                                fg_color=("white", "#1b2a4a"),
                                border_width=1, border_color=("gray80", "#2a3f6f"))
            card.grid(row=idx_c // 3, column=idx_c % 3, padx=10, pady=10, sticky="nsew")
            ctk.CTkLabel(card, text="📖", font=ctk.CTkFont(size=28)).pack(pady=(16, 4))
            ctk.CTkLabel(card, text=curso["name"],
                         font=ctk.CTkFont(size=12, weight="bold"),
                         wraplength=200, justify="center").pack(padx=12)
            ctk.CTkLabel(card, text=f"{total_c} tareas  ·  {total_c - entregadas_c} pendientes",
                         font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(4, 6))
            pb = ctk.CTkProgressBar(card, height=8, corner_radius=4, progress_color="#4fc3f7")
            pb.pack(fill="x", padx=20, pady=(0, 4))
            pb.set(prog_c)
            ctk.CTkLabel(card, text=f"{int(prog_c * 100)}% entregado",
                         font=ctk.CTkFont(size=10), text_color="#4fc3f7").pack(pady=(0, 14))

    # ═══════════════════════════════════════════════════════════════════════════
    # VISTA 2 — TAREAS: lista plana de todas las tareas
    # ═══════════════════════════════════════════════════════════════════════════
    vista_tareas = ctk.CTkFrame(main, corner_radius=0, fg_color="transparent")
    vista_tareas.grid_rowconfigure(0, weight=1)
    vista_tareas.grid_columnconfigure(0, weight=1)

    tree_tareas = ttk.Treeview(vista_tareas, style="Moodle.Treeview", show="headings")
    tree_tareas["columns"] = ("Curso", "Tarea", "Estado", "Fecha")
    for col, w, anc in [("Curso", 220, "w"), ("Tarea", 280, "w"),
                        ("Estado", 150, "center"), ("Fecha", 140, "center")]:
        tree_tareas.column(col, width=w, anchor=anc)
        tree_tareas.heading(col, text=col)
    tree_tareas.tag_configure("entregada", foreground="#81c784")
    tree_tareas.tag_configure("pendiente", foreground="#ffb74d")

    sb_t = ctk.CTkScrollbar(vista_tareas, command=tree_tareas.yview)
    tree_tareas.configure(yscrollcommand=sb_t.set)
    tree_tareas.grid(row=0, column=0, sticky="nsew")
    sb_t.grid(row=0, column=1, sticky="ns")

    def _poblar_tareas():
        for item in tree_tareas.get_children():
            tree_tareas.delete(item)
        for curso in estado["courses"]:
            for tarea in curso.get("assignments", []):
                est = tarea.get("estado_entrega", "—")
                tag = "entregada" if "entregad" in est.lower() else "pendiente"
                tree_tareas.insert("", "end",
                                   values=(curso["name"], tarea["name"],
                                           est, tarea.get("due_date", "—")),
                                   tags=(tag,))

    _poblar_tareas()

    # ═══════════════════════════════════════════════════════════════════════════
    # VISTA 3 — PROGRESO: barras por curso
    # ═══════════════════════════════════════════════════════════════════════════
    vista_progreso = ctk.CTkScrollableFrame(main, fg_color="transparent")

    def _poblar_progreso():
        for w in vista_progreso.winfo_children():
            w.destroy()
        for curso in estado["courses"]:
            asgs = curso.get("assignments", [])
            total_c = len(asgs)
            entregadas_c = sum(1 for a in asgs if "entregad" in a.get("estado_entrega", "").lower())
            prog_c = entregadas_c / total_c if total_c > 0 else 0
            row_f = ctk.CTkFrame(vista_progreso, fg_color=("white", "#1b2a4a"),
                                 corner_radius=10, border_width=1,
                                 border_color=("gray80", "#2a3f6f"))
            row_f.pack(fill="x", padx=10, pady=5)
            top_f = ctk.CTkFrame(row_f, fg_color="transparent")
            top_f.pack(fill="x", padx=14, pady=(10, 2))
            ctk.CTkLabel(top_f, text=curso["name"],
                         font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left")
            ctk.CTkLabel(top_f, text=f"{entregadas_c}/{total_c}",
                         font=ctk.CTkFont(size=12), text_color="gray").pack(side="right")
            pb = ctk.CTkProgressBar(row_f, height=12, corner_radius=6, progress_color="#4fc3f7")
            pb.pack(fill="x", padx=14, pady=(0, 10))
            pb.set(prog_c)

    # ═══════════════════════════════════════════════════════════════════════════
    # VISTA 4 — AJUSTES
    # ═══════════════════════════════════════════════════════════════════════════
    vista_ajustes = ctk.CTkFrame(main, corner_radius=0, fg_color="transparent")
    aj_inner = ctk.CTkFrame(vista_ajustes, corner_radius=16,
                            fg_color=("white", "#1b2a4a"),
                            border_width=1, border_color=("gray80", "#2a3f6f"))
    aj_inner.pack(padx=30, pady=30, fill="x")
    ctk.CTkLabel(aj_inner, text="⚙️  Ajustes",
                 font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=20, pady=(20, 10))
    ctk.CTkFrame(aj_inner, height=1, fg_color="#2a3f6f").pack(fill="x", padx=20)
    aj_row = ctk.CTkFrame(aj_inner, fg_color="transparent")
    aj_row.pack(fill="x", padx=20, pady=16)
    ctk.CTkLabel(aj_row, text="Tema de la aplicación",
                 font=ctk.CTkFont(size=13)).pack(side="left")
    ctk.CTkButton(aj_row, text="Cambiar tema", width=140, height=34,
                  corner_radius=8, fg_color="#2a2a4a", hover_color="#3a3a6a",
                  font=ctk.CTkFont(size=12), command=toggle_tema).pack(side="right")
    ctk.CTkLabel(aj_inner, text=f"Provincia activa: {provincia_nombre}",
                 font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=20, pady=(0, 20))

    # ═══════════════════════════════════════════════════════════════════════════
    # SISTEMA DE VISTAS: mostrar/ocultar según nav
    # ═══════════════════════════════════════════════════════════════════════════
    vistas = [vista_inicio, vista_cursos, vista_tareas, vista_progreso, vista_ajustes]

    def refrescar_vista(idx):
        if idx == 1:
            _poblar_cursos()
        elif idx == 3:
            _poblar_progreso()

    for v in vistas:
        v.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        v.grid_remove()
    vista_inicio.grid()   # Vista por defecto

    # ========== POLLING: refrescar cuando el hilo termine ==========
    def check_actualizacion():
        if resultado is not None and resultado.get("courses") is not None:
            estado["courses"] = resultado["courses"]
            poblar_arbol(search_var.get())
            _poblar_tareas()
            actualizar_cards()
            carga_label.configure(text="✅ Datos actualizados", text_color="#81c784")
            app.after(3000, lambda: carga_label.configure(text=""))
        else:
            app.after(1000, check_actualizacion)

    if resultado is not None:
        app.after(1000, check_actualizacion)

    app.protocol("WM_DELETE_WINDOW", lambda: (app.destroy(), driver_quit_fn()))
    app.mainloop()