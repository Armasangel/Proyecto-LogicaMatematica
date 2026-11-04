"""Firma configurable de constantes, funciones y predicados."""

import re
from collections.abc import Mapping
from types import MappingProxyType

from errores import ErrorLenguaje


def validar_nombre(nombre, ruta="lenguaje"):
    if (not isinstance(nombre, str)
            or re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", nombre) is None
            or nombre in {"forall", "exists"}):
        raise ErrorLenguaje(f"Nombre de símbolo inválido: {nombre!r}.", ruta=ruta)


class Lenguaje:
    def __init__(self, constantes=(), funciones=None, predicados=None):
        if isinstance(constantes, (str, bytes)):
            raise ErrorLenguaje("Las constantes deben ser una colección de nombres.", ruta="constantes")
        try:
            nombres = list(constantes)
        except TypeError as exc:
            raise ErrorLenguaje("Las constantes deben ser una colección de nombres.", ruta="constantes") from exc
        for nombre in nombres:
            validar_nombre(nombre, "constantes")
        if len(set(nombres)) != len(nombres):
            raise ErrorLenguaje("Hay constantes duplicadas.", ruta="constantes")
        self.constantes = frozenset(nombres)
        self.funciones = MappingProxyType(self._aridades(funciones, "funciones"))
        self.predicados = MappingProxyType(self._aridades(predicados, "predicados"))
        if (self.constantes & self.funciones.keys()
                or self.constantes & self.predicados.keys()
                or self.funciones.keys() & self.predicados.keys()):
            raise ErrorLenguaje("Un símbolo no puede tener más de una categoría.", ruta="lenguaje")

    @staticmethod
    def _aridades(datos, categoria):
        if datos is None:
            return {}
        if not isinstance(datos, Mapping):
            raise ErrorLenguaje("Se esperaba un diccionario nombre: aridad.", ruta=categoria)
        salida = {}
        for nombre, aridad in datos.items():
            validar_nombre(nombre, categoria)
            if type(aridad) is not int or aridad < 0:
                raise ErrorLenguaje("La aridad debe ser un entero mayor o igual a cero.", ruta=f"{categoria}.{nombre}")
            salida[nombre] = aridad
        return salida

    @property
    def simbolos(self):
        return self.constantes | self.funciones.keys() | self.predicados.keys()


def lenguaje_ejemplo():
    """Coincide con interpretacion_ejemplo() del evaluador existente."""
    return Lenguaje(constantes=("a", "b"), funciones={"s": 1, "suma": 2},
                    predicados={"P": 1, "M": 2})
