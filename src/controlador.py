from resultado import Resultado

# Los módulos de sintaxis y evaluación son opcionales: si falta alguno,
# la interfaz igual abre y muestra un error claro.
try:
    from analizador_sintactico import AnalizadorSintactico
except ImportError:
    AnalizadorSintactico = None

try:
    from evaluador import Evaluador
except ImportError:
    Evaluador = None


class Controlador:
    # Conecta la interfaz con los módulos de sintaxis y semántica.

    def __init__(self):
        self.analizador = AnalizadorSintactico() if AnalizadorSintactico else None
        self.evaluador = Evaluador() if Evaluador else None

    def configurar(self, lenguaje, interpretacion):
        # Fija el lenguaje y la interpretación ingresados por el usuario.
        self.analizador = AnalizadorSintactico(lenguaje)
        self.evaluador = Evaluador(interpretacion)

    def variables_libres(self, texto):
        # Analiza la fórmula y devuelve sus variables libres (puede lanzar errores).
        return self.analizador.analizar_con_variables(texto)[1]

    def evaluar(self, texto, entorno=None):
        texto = texto.strip()
        if not texto:
            return Resultado.error("La fórmula está vacía.")

        if self.analizador is None:
            return Resultado.error("Falta el módulo de sintaxis.")
        if self.evaluador is None:
            return Resultado.error("Falta el módulo de evaluación.")

        try:
            arbol = self.analizador.analizar(texto)
            evaluador = self.evaluador
            if entorno is not None:
                evaluador = Evaluador(evaluador.interpretacion, entorno)
            valor, explicacion = evaluador.evaluar(arbol)
            return Resultado(valor=valor, explicacion=explicacion)
        except Exception as e:
            return Resultado.desde_excepcion(e, prefijo="Error: ")
