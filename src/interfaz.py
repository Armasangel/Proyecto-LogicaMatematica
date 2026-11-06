import tkinter as tk
from tkinter import ttk

import entrada_datos as datos
from errores import ErrorValidacion
from estilo import COLOR_BOTON, COLOR_FONDO, COLOR_PRIMARIO, COLOR_TARJETA, FUENTE
from panel_resultado import PanelResultado
from paneles_entrada import PanelFormula, PanelInterpretacion, PanelLenguaje
from resultado import Resultado

PESTANA_LENGUAJE, PESTANA_INTERPRETACION, PESTANA_FORMULA = 0, 1, 2


class VentanaPrincipal(tk.Tk):
    """Ventana principal: lenguaje, interpretación, fórmula con entorno y resultado."""

    def __init__(self, controlador):
        super().__init__()
        self.controlador = controlador

        self.title("Evaluador de Lógica de Primer Orden")
        self.geometry("920x860")
        self.minsize(760, 680)
        self.configure(bg=COLOR_FONDO)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=3)
        self.rowconfigure(2, weight=2)

        self._construir_cuaderno()
        self._construir_barra()
        self.panel_resultado = PanelResultado(self)
        self.panel_resultado.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.cargar_ejemplo()

    # ---------- construcción ----------

    def _construir_cuaderno(self):
        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.grid(row=0, column=0, sticky="nsew", padx=24, pady=(24, 8))
        self.p_lenguaje = PanelLenguaje(self.cuaderno, self._aplicar_lenguaje)
        self.p_interp = PanelInterpretacion(self.cuaderno)
        self.p_formula = PanelFormula(self.cuaderno, self.evaluar)
        self.cuaderno.add(self.p_lenguaje, text="  1 · Lenguaje  ")
        self.cuaderno.add(self.p_interp, text="  2 · Interpretación  ")
        self.cuaderno.add(self.p_formula, text="  3 · Fórmula y entorno  ")
        self.cuaderno.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)

    def _construir_barra(self):
        barra = tk.Frame(self, bg=COLOR_FONDO)
        barra.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        for texto, comando in (("Cargar ejemplo", self.cargar_ejemplo),
                               ("Borrar fórmula", self._borrar_formula)):
            tk.Button(barra, text=texto, command=comando, font=(FUENTE, 11),
                      bg=COLOR_BOTON, relief="flat", padx=12, pady=4,
                      cursor="hand2").pack(side="left", padx=(0, 8))
        tk.Button(barra, text="Evaluar", command=self.evaluar,
                  font=(FUENTE, 12, "bold"), bg=COLOR_PRIMARIO, fg="white",
                  activebackground="#155ab6", activeforeground="white",
                  relief="flat", padx=24, pady=6, cursor="hand2").pack(side="right")

    # ---------- acciones ----------

    def cargar_ejemplo(self):
        e = datos.ejemplo()
        self.p_lenguaje.cargar(*e["lenguaje"])
        self.p_interp.sincronizar(datos.construir_lenguaje(*e["lenguaje"]))
        self.p_interp.cargar(e["dominio"], e["constantes"], e["funciones"], e["relaciones"])
        self.p_formula.cargar(e["formula"])
        self.p_formula.mostrar_libres(set(), [])
        self.panel_resultado.limpiar()

    def _borrar_formula(self):
        self.p_formula.borrar_todo()
        self.p_formula.mostrar_libres(set(), [])
        self.panel_resultado.limpiar()

    def _aplicar_lenguaje(self):
        try:
            lenguaje = datos.construir_lenguaje(*self.p_lenguaje.leer())
        except ErrorValidacion as exc:
            return self._mostrar(Resultado.desde_excepcion(exc))
        self.p_interp.sincronizar(lenguaje)
        self.panel_resultado.limpiar()
        self.cuaderno.select(PESTANA_INTERPRETACION)

    def _al_cambiar_pestana(self, _evento):
        if self.cuaderno.index("current") == PESTANA_INTERPRETACION:
            try:
                self.p_interp.sincronizar(datos.construir_lenguaje(*self.p_lenguaje.leer()))
            except ErrorValidacion:
                pass  # el error se mostrará al evaluar o al aplicar el lenguaje

    def evaluar(self):
        """Lenguaje → interpretación → fórmula → entorno → valor de verdad."""
        try:
            lenguaje = datos.construir_lenguaje(*self.p_lenguaje.leer())
            self.p_interp.sincronizar(lenguaje)
            interpretacion = datos.construir_interpretacion(lenguaje, *self.p_interp.leer())
            self.controlador.configurar(lenguaje, interpretacion)

            texto = self.p_formula.texto()
            libres = self.controlador.variables_libres(texto)
            self.p_formula.mostrar_libres(libres, interpretacion.dominio)
            entorno = datos.construir_entorno(self.p_formula.leer_entorno())
        except ErrorValidacion as exc:
            return self._mostrar(Resultado.desde_excepcion(exc))
        self._mostrar(self.controlador.evaluar(texto, entorno))

    # ---------- resultado ----------

    def _mostrar(self, resultado):
        self.panel_resultado.mostrar(resultado)
        if resultado.es_error:
            self.cuaderno.select(self._pestana_del_error(resultado))

    @staticmethod
    def _pestana_del_error(res):
        ruta = res.ruta or ""
        if res.tipo == "ErrorLenguaje":
            return PESTANA_LENGUAJE
        if res.tipo in ("ErrorSintaxis", "ErrorLexico") or ruta.startswith(("formula", "entorno")):
            return PESTANA_FORMULA
        if ruta.startswith(("dominio", "constantes", "funciones", "relaciones")):
            return PESTANA_INTERPRETACION
        return PESTANA_FORMULA
