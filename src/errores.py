"""Errores de entrada con ubicación para la interfaz."""


class ErrorValidacion(ValueError):
    def __init__(self, mensaje, *, posicion=None, texto=None, ruta=None):
        self.mensaje = mensaje
        self.posicion = posicion  # Índice desde cero dentro de la fórmula.
        self.texto = texto
        self.ruta = ruta
        self.linea = self.columna = None
        detalle = mensaje
        if ruta:
            detalle += f" [{ruta}]"
        if posicion is not None and texto is not None:
            self.linea = texto.count("\n", 0, posicion) + 1
            inicio = texto.rfind("\n", 0, posicion) + 1
            self.columna = posicion - inicio + 1
            fin = texto.find("\n", posicion)
            fragmento = texto[inicio:fin if fin >= 0 else len(texto)]
            detalle += (f" (línea {self.linea}, columna {self.columna}, "
                        f"posición {posicion + 1})\n{fragmento}\n"
                        + " " * (self.columna - 1) + "^")
        super().__init__(detalle)


class ErrorSintaxis(ErrorValidacion):
    pass


class ErrorLexico(ErrorSintaxis):
    pass


class ErrorLenguaje(ErrorValidacion):
    pass


class ErrorSemantico(ErrorValidacion):
    pass
