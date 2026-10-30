import tkinter as tk

SIMBOLOS = ["¬", "∧", "∨", "→", "∀", "∃", "(", ")"]


class TecladoLogico(tk.Frame):
    """Fila de botones con los símbolos lógicos, como una calculadora."""

    def __init__(self, padre, al_presionar, al_borrar):
        super().__init__(padre, bg="#ffffff")
        self.al_presionar = al_presionar
        self.al_borrar = al_borrar
        self._crear_botones()

    def _crear_botones(self):
        for simbolo in SIMBOLOS:
            self._crear_boton(simbolo, lambda s=simbolo: self.al_presionar(s))
        self._crear_boton("⌫", self.al_borrar)

    def _crear_boton(self, texto, accion):
        tk.Button(
            self, text=texto, command=accion,
            font=("Segoe UI", 14), width=3,
            bg="#f1f1f3", activebackground="#dcdce0",
            relief="flat", cursor="hand2",
        ).pack(side="left", padx=3)