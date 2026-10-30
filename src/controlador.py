from resultado import Resultado

# Los módulos de Persona 1 y Persona 2 son opcionales por ahora.
# Si todavía no existen, la interfaz igual funciona.
try:
    from analizador_sintactico import AnalizadorSintactico
except ImportError:
    AnalizadorSintactico = None

try:
    from evaluador import Evaluador
except ImportError:
    Evaluador = None


class Controlador:
    """Conecta la interfaz con los módulos de sintaxis y semántica."""

    def __init__(self):
        self.analizador = AnalizadorSintactico() if AnalizadorSintactico else None
        self.evaluador = Evaluador() if Evaluador else None

    def evaluar(self, texto):
        texto = texto.strip()
        if not texto:
            return Resultado.error("La fórmula está vacía.")

        if self.analizador is None:
            return Resultado.error("Falta el módulo de sintaxis (Persona 2).")
        if self.evaluador is None:
            return Resultado.error("Falta el módulo de evaluación (Persona 1).")

        try:
            arbol = self.analizador.analizar(texto)
            valor, explicacion = self.evaluador.evaluar(arbol)
            return Resultado(valor=valor, explicacion=explicacion)
        except Exception as e:
            return Resultado.error(f"Error: {e}")