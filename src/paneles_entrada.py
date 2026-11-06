# Paneles gráficos para ingresar el lenguaje, la interpretación y la fórmula.

import tkinter as tk
from tkinter import ttk

from entrada_datos import parsear_dominio, plantilla_funcion
from estilo import COLOR_AYUDA, COLOR_BOTON, COLOR_CAMPO, COLOR_TARJETA, FUENTE
from teclado_logico import TecladoLogico


def _etiqueta(padre, texto, negrita=True, color="black", **pack):
    tk.Label(padre, text=texto, bg=COLOR_TARJETA, fg=color,
             font=(FUENTE, 11, "bold" if negrita else "normal"),
             justify="left").pack(anchor="w", **pack)


def _boton(padre, texto, comando):
    return tk.Button(padre, text=texto, command=comando, font=(FUENTE, 10),
                     bg=COLOR_BOTON, relief="flat", padx=10, pady=3, cursor="hand2")


class FrameDesplazable(tk.Frame):
    # Contenedor con barra de desplazamiento vertical.

    def __init__(self, padre):
        super().__init__(padre, bg=COLOR_TARJETA)
        self.canvas = tk.Canvas(self, bg=COLOR_TARJETA, highlightthickness=0)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interior = tk.Frame(self.canvas, bg=COLOR_TARJETA)
        ventana = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.interior.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            ventana, width=e.width))
        self.canvas.configure(yscrollcommand=barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.bind("<Enter>", lambda e: self._rueda(True))
        self.bind("<Leave>", lambda e: self._rueda(False))

    def _rueda(self, activar):
        eventos = ("<MouseWheel>", "<Button-4>", "<Button-5>")
        for ev in eventos:
            if activar:
                self.bind_all(ev, self._desplazar)
            else:
                self.unbind_all(ev)

    def _desplazar(self, evento):
        if isinstance(evento.widget, tk.Text):
            return
        paso = -1 if (evento.num == 4 or evento.delta > 0) else 1
        self.canvas.yview_scroll(paso, "units")


# Lenguaje

class PanelLenguaje(tk.Frame):
    CAMPOS = (
        ("constantes", "Constantes", "Nombres separados por coma. Ej.: a, b"),
        ("funciones", "Símbolos funcionales", "nombre/aridad separados por coma. Ej.: s/1, suma/2"),
        ("predicados", "Predicados", "nombre/aridad separados por coma. Ej.: P/1, M/2"),
    )

    def __init__(self, padre, al_aplicar):
        super().__init__(padre, bg=COLOR_TARJETA, padx=20, pady=14)
        self._campos = {}
        for clave, titulo, ayuda in self.CAMPOS:
            _etiqueta(self, titulo)
            campo = tk.Entry(self, font=(FUENTE, 12), bg=COLOR_CAMPO, relief="flat")
            campo.pack(fill="x", ipady=6, pady=(4, 0))
            _etiqueta(self, ayuda, negrita=False, color=COLOR_AYUDA, pady=(2, 10))
            self._campos[clave] = campo
        _boton(self, "Aplicar lenguaje →", al_aplicar).pack(anchor="e")

    def leer(self):
        return tuple(self._campos[c].get() for c, _, _ in self.CAMPOS)

    def cargar(self, constantes, funciones, predicados):
        for clave, texto in zip(("constantes", "funciones", "predicados"),
                                (constantes, funciones, predicados)):
            self._campos[clave].delete(0, tk.END)
            self._campos[clave].insert(0, texto)


# Interpretación

class PanelInterpretacion(tk.Frame):
    def __init__(self, padre):
        super().__init__(padre, bg=COLOR_TARJETA, padx=20, pady=10)
        _etiqueta(self, "Dominio 𝒟 (finito, no vacío)")
        self.dominio = tk.Entry(self, font=(FUENTE, 12), bg=COLOR_CAMPO, relief="flat")
        self.dominio.pack(fill="x", ipady=5, pady=(4, 0))
        _etiqueta(self, "Elementos separados por coma. Ej.: 1, 2, 3, 4 (los números se leen como enteros)",
                  negrita=False, color=COLOR_AYUDA, pady=(2, 6))

        barra = tk.Frame(self, bg=COLOR_TARJETA)
        barra.pack(fill="x", pady=(0, 4))
        _boton(barra, "Rellenar tablas de funciones vacías",
               self.generar_plantillas).pack(side="left")
        self.mensaje = tk.Label(barra, text="", bg=COLOR_TARJETA, fg="#b06000",
                                font=(FUENTE, 10))
        self.mensaje.pack(side="left", padx=10)

        self.desplazable = FrameDesplazable(self)
        self.desplazable.pack(fill="both", expand=True)
        self._aridades = {}
        self._constantes, self._funciones, self._relaciones = {}, {}, {}

    # construcción dinámica según el lenguaje
    def sincronizar(self, lenguaje):
        previo = self.leer()
        for hijo in self.desplazable.interior.winfo_children():
            hijo.destroy()
        self._constantes, self._funciones, self._relaciones = {}, {}, {}
        self._aridades = {}
        interior = self.desplazable.interior

        for c in sorted(lenguaje.constantes):
            fila = tk.Frame(interior, bg=COLOR_TARJETA)
            fila.pack(fill="x", pady=2)
            _etiqueta(fila, f"{c}^ℐ =", pady=0)
            fila.winfo_children()[0].pack_configure(side="left")
            e = tk.Entry(fila, font=(FUENTE, 11), bg=COLOR_CAMPO, relief="flat", width=14)
            e.pack(side="left", padx=8, ipady=3)
            e.insert(0, previo[1].get(c, ""))
            self._constantes[c] = e

        for n, a in sorted(lenguaje.funciones.items()):
            self._aridades[n] = a
            self._funciones[n] = self._caja(
                interior, f"{n}^ℐ : 𝒟^{a} → 𝒟     (una línea por entrada:  "
                          f"{', '.join(['d'] * a) or '()'} -> valor)", previo[2].get(n, ""))
        for n, a in sorted(lenguaje.predicados.items()):
            self._relaciones[n] = self._caja(
                interior, f"{n}^ℐ ⊆ 𝒟^{a}     (una tupla por línea:  "
                          f"({', '.join(['d'] * a)}))", previo[3].get(n, ""))

    def _caja(self, padre, titulo, contenido):
        _etiqueta(padre, titulo, pady=(8, 2))
        caja = tk.Text(padre, height=5, font=(FUENTE, 11), bg=COLOR_CAMPO,
                       relief="flat", padx=6, pady=4)
        caja.pack(fill="x")
        caja.insert("1.0", contenido)
        return caja

    # lectura y carga
    def leer(self):
        return (
            self.dominio.get(),
            {n: e.get() for n, e in self._constantes.items()},
            {n: t.get("1.0", "end-1c") for n, t in self._funciones.items()},
            {n: t.get("1.0", "end-1c") for n, t in self._relaciones.items()},
        )

    def cargar(self, dominio, constantes, funciones, relaciones):
        self.dominio.delete(0, tk.END)
        self.dominio.insert(0, dominio)
        for e_dic, datos in ((self._constantes, constantes),):
            for n, e in e_dic.items():
                e.delete(0, tk.END)
                e.insert(0, datos.get(n, ""))
        for t_dic, datos in ((self._funciones, funciones), (self._relaciones, relaciones)):
            for n, t in t_dic.items():
                t.delete("1.0", tk.END)
                t.insert("1.0", datos.get(n, ""))

    def generar_plantillas(self):
        self.mensaje.configure(text="")
        try:
            dominio = parsear_dominio(self.dominio.get())
            if not dominio:
                raise ValueError("Escriba primero el dominio.")
            for n, caja in self._funciones.items():
                if not caja.get("1.0", "end-1c").strip():
                    caja.insert("1.0", plantilla_funcion(dominio, self._aridades[n]))
        except Exception as exc:
            self.mensaje.configure(text=str(exc))


# Fórmula

class PanelFormula(tk.Frame):
    def __init__(self, padre, al_evaluar):
        super().__init__(padre, bg=COLOR_TARJETA, padx=20, pady=14)
        _etiqueta(self, "Fórmula")
        self.entrada = tk.Entry(self, font=(FUENTE, 14), bg=COLOR_CAMPO,
                                relief="flat", insertwidth=2)
        self.entrada.pack(fill="x", pady=(6, 10), ipady=8)
        self.entrada.bind("<Return>", lambda e: al_evaluar())
        self.entrada.focus_set()

        TecladoLogico(self, al_presionar=self.insertar,
                      al_borrar=self.borrar_caracter).pack(fill="x")
        _etiqueta(self, "También puede escribir con el teclado: ~ ! & | -> forall exists",
                  negrita=False, color=COLOR_AYUDA, pady=(6, 10))

        self.etiqueta_libres = tk.Label(self, text="Variables libres: (aún sin analizar)",
                                        bg=COLOR_TARJETA, font=(FUENTE, 11, "bold"))
        self.etiqueta_libres.pack(anchor="w")
        self.marco_entorno = tk.Frame(self, bg=COLOR_TARJETA)
        self.marco_entorno.pack(fill="x", pady=(4, 0))
        self._combos = {}

    def texto(self):
        return self.entrada.get()

    def cargar(self, formula):
        self.entrada.delete(0, tk.END)
        self.entrada.insert(0, formula)

    # entorno σ para las variables libres
    def mostrar_libres(self, libres, dominio):
        previo = self.leer_entorno()
        for hijo in self.marco_entorno.winfo_children():
            hijo.destroy()
        self._combos = {}
        if not libres:
            self.etiqueta_libres.configure(text="Variables libres: ninguna (fórmula cerrada, no necesita entorno)")
            return
        self.etiqueta_libres.configure(
            text="Variables libres: " + ", ".join(sorted(libres))
                 + "   —   elija un valor de 𝒟 para cada una (entorno σ)")
        valores = [str(d) for d in dominio]
        for fila, v in enumerate(sorted(libres)):
            tk.Label(self.marco_entorno, text=f"σ({v}) =", bg=COLOR_TARJETA,
                     font=(FUENTE, 11)).grid(row=fila, column=0, sticky="w", pady=2)
            combo = ttk.Combobox(self.marco_entorno, values=valores, width=14,
                                 font=(FUENTE, 11))
            combo.grid(row=fila, column=1, padx=8, pady=2)
            combo.set(previo.get(v, ""))
            self._combos[v] = combo

    def leer_entorno(self):
        return {v: c.get() for v, c in self._combos.items()}

    # edición
    def insertar(self, simbolo):
        if self.entrada.selection_present():
            self.entrada.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.entrada.insert(tk.INSERT, simbolo)
        self.entrada.focus_set()

    def borrar_caracter(self):
        if self.entrada.selection_present():
            self.entrada.delete(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            pos = self.entrada.index(tk.INSERT)
            if pos > 0:
                self.entrada.delete(pos - 1)
        self.entrada.focus_set()

    def borrar_todo(self):
        self.entrada.delete(0, tk.END)
        self.entrada.focus_set()
