"""Adaptador: conserva el evaluador original y antepone la validación."""

import importlib.util
from pathlib import Path

from interpretacion import Entorno, ErrorSemantico, Interpretacion
from nodos import variables_libres
from validacion import validar_entrada, validar_termino


_ruta_original = Path(__file__).resolve().parents[1] / "evaluador.py"
_spec = importlib.util.spec_from_file_location("_evaluador_persona1", _ruta_original)
if _spec is None or _spec.loader is None:
    raise ImportError(f"No se pudo cargar el evaluador original: {_ruta_original}")
_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_original)
Juicio = _original.Juicio
interpretacion_ejemplo = _original.interpretacion_ejemplo


class Evaluador(_original.Evaluador):
    def __init__(self, interpretacion=None, entorno=None):
        if interpretacion is not None and not isinstance(interpretacion, Interpretacion):
            raise ErrorSemantico("Se esperaba una Interpretacion válida.")
        sigma = entorno if isinstance(entorno, Entorno) else Entorno(entorno)
        super().__init__(interpretacion, sigma)

    def evaluar(self, arbol):
        # Un intento inválido no conserva el juicio de una evaluación anterior.
        self.ultimo_juicio = None
        return super().evaluar(arbol)

    def evaluar_formula(self, formula, sigma=None):
        self.ultimo_juicio = None
        sigma = validar_entrada(formula, self.interpretacion,
                                self.entorno if sigma is None else sigma)
        return super().evaluar_formula(formula, sigma)

    def evaluar_termino(self, termino, sigma=None):
        sigma = self.entorno if sigma is None else sigma
        sigma = sigma if isinstance(sigma, Entorno) else Entorno(sigma)
        validar_termino(termino, self.interpretacion.lenguaje)
        sigma.validar(self.interpretacion.dominio, variables_libres(termino),
                      lenguaje=self.interpretacion.lenguaje)
        return super().evaluar_termino(termino, sigma)
