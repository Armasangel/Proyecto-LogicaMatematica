class Resultado:
    """Lo que la interfaz recibe después de evaluar una fórmula."""

    def __init__(self, valor=None, explicacion="", errores=None):
        self.valor = valor              # True / False / None
        self.explicacion = explicacion  # texto de la Persona 1
        self.errores = errores or []    # mensajes de la Persona 2

    @property
    def es_error(self):
        return len(self.errores) > 0

    @classmethod
    def error(cls, mensaje):
        return cls(errores=[mensaje])