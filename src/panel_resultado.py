import tkinter as tk

COLOR_VERDADERO = "#1e8e3e"
COLOR_FALSO = "#d93025"
COLOR_ERROR = "#b06000"


class PanelResultado(tk.Frame):
    """Muestra Verdadero/Falso, la explicación o los errores."""

    def __init__(self, padre):
        super().__init__(padre, bg="#ffffff", padx=24, pady=16)

        tk.Label(
            self, text="Resultado", bg="#ffffff",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")

        self.etiqueta_valor = tk.Label(
            self, text="—", bg="#ffffff", font=("Segoe UI", 18, "bold"),
        )
        self.etiqueta_valor.pack(anchor="w", pady=(4, 8))

        self.texto = tk.Text(
            self, height=6, wrap="word", font=("Segoe UI", 11),
            bg="#f7f7f9", relief="flat", padx=8, pady=8,
        )
        self.texto.pack(fill="both", expand=True)
        self.texto.configure(state="disabled")

    def mostrar(self, resultado):
        if resultado.es_error:
            self.etiqueta_valor.configure(text="Error", fg=COLOR_ERROR)
            self._escribir("\n".join(resultado.errores))
        elif resultado.valor:
            self.etiqueta_valor.configure(text="Verdadero", fg=COLOR_VERDADERO)
            self._escribir(resultado.explicacion)
        else:
            self.etiqueta_valor.configure(text="Falso", fg=COLOR_FALSO)
            self._escribir(resultado.explicacion)

    def limpiar(self):
        self.etiqueta_valor.configure(text="—", fg="black")
        self._escribir("")

    def _escribir(self, contenido):
        self.texto.configure(state="normal")
        self.texto.delete("1.0", tk.END)
        self.texto.insert("1.0", contenido)
        self.texto.configure(state="disabled")