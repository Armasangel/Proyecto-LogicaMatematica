import tkinter as tk

from teclado_logico import TecladoLogico
from panel_resultado import PanelResultado

COLOR_FONDO = "#cfe0fb"
COLOR_TARJETA = "#ffffff"
COLOR_CAMPO = "#e9e9ec"
COLOR_BOTON = "#f1f1f3"
COLOR_PRIMARIO = "#1a73e8"
FUENTE = "Segoe UI"


class VentanaPrincipal(tk.Tk):
    """Ventana principal: campo de la fórmula, teclado lógico y resultado."""

    def __init__(self, controlador):
        super().__init__()
        self.controlador = controlador

        self.title("Evaluador de Lógica de Primer Orden")
        self.geometry("760x520")
        self.configure(bg=COLOR_FONDO)

        self._construir_tarjeta()
        self._construir_panel_resultado()

    def _construir_tarjeta(self):
        tarjeta = tk.Frame(self, bg=COLOR_TARJETA, padx=24, pady=20)
        tarjeta.pack(fill="x", padx=40, pady=(40, 16))

        tk.Label(
            tarjeta, text="Fórmula", bg=COLOR_TARJETA,
            font=(FUENTE, 13, "bold"),
        ).pack(anchor="w")

        self.entrada = tk.Entry(
            tarjeta, font=(FUENTE, 14), bg=COLOR_CAMPO,
            relief="flat", insertwidth=2,
        )
        self.entrada.pack(fill="x", pady=(8, 12), ipady=8)
        self.entrada.bind("<Return>", lambda evento: self._evaluar())
        self.entrada.focus_set()

        self.teclado = TecladoLogico(
            tarjeta,
            al_presionar=self._insertar_simbolo,
            al_borrar=self._borrar_caracter,
        )
        self.teclado.pack(fill="x")

        barra = tk.Frame(tarjeta, bg=COLOR_TARJETA)
        barra.pack(fill="x", pady=(14, 0))

        tk.Button(
            barra, text="Borrar todo", command=self._borrar_todo,
            font=(FUENTE, 11), bg=COLOR_BOTON, relief="flat",
            padx=12, pady=4, cursor="hand2",
        ).pack(side="left")

        tk.Button(
            barra, text="Evaluar", command=self._evaluar,
            font=(FUENTE, 12, "bold"), bg=COLOR_PRIMARIO, fg="white",
            activebackground="#155ab6", activeforeground="white",
            relief="flat", padx=24, pady=6, cursor="hand2",
        ).pack(side="right")

    def _construir_panel_resultado(self):
        self.panel_resultado = PanelResultado(self)
        self.panel_resultado.pack(fill="both", expand=True, padx=40, pady=(0, 30))

    # ---------- Acciones ----------

    def _insertar_simbolo(self, simbolo):
        if self.entrada.selection_present():
            self.entrada.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.entrada.insert(tk.INSERT, simbolo)
        self.entrada.focus_set()

    def _borrar_caracter(self):
        if self.entrada.selection_present():
            self.entrada.delete(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            posicion = self.entrada.index(tk.INSERT)
            if posicion > 0:
                self.entrada.delete(posicion - 1)
        self.entrada.focus_set()

    def _borrar_todo(self):
        self.entrada.delete(0, tk.END)
        self.panel_resultado.limpiar()
        self.entrada.focus_set()

    def _evaluar(self):
        resultado = self.controlador.evaluar(self.entrada.get())
        self.panel_resultado.mostrar(resultado)