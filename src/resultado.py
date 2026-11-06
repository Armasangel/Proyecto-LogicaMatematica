class Resultado:
    # Lo que la interfaz recibe después de evaluar una fórmula.

    def __init__(self, valor=None, explicacion="", errores=None, ruta=None, tipo=None):
        self.valor = valor              # True / False / None
        self.explicacion = explicacion  # justificación del evaluador
        self.errores = errores or []    # mensajes de validación
        self.ruta = ruta                # dónde está el error (p. ej. "funciones.s")
        self.tipo = tipo                # clase de la excepción (p. ej. "ErrorLenguaje")

    @property
    def es_error(self):
        return len(self.errores) > 0

    @classmethod
    def error(cls, mensaje, ruta=None, tipo=None):
        return cls(errores=[mensaje], ruta=ruta, tipo=tipo)

    @classmethod
    def desde_excepcion(cls, exc, prefijo=""):
        return cls.error(f"{prefijo}{exc}", ruta=getattr(exc, "ruta", None),
                         tipo=type(exc).__name__)
