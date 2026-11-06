# """Convierte el texto escrito en la interfaz en Lenguaje, Interpretacion y Entorno.

# Formatos (los números se leen como enteros; cualquier otro texto es un elemento):
#   dominio      1, 2, 3, 4
#   firmas       s/1, suma/2            (nombre/aridad)
#   función      una línea por entrada:  1, 2 -> 3
#   relación     una tupla por línea (o separadas por ';'):  (1, 2)

import re
from itertools import product

from errores import ErrorLenguaje, ErrorSemantico
from interpretacion import Entorno, Interpretacion
from lenguaje import Lenguaje

_NOMBRE = r"[A-Za-z_][A-Za-z_0-9]*"
_FLECHA = re.compile(r"\s*(?:->|→|↦|=)\s*")
MAX_FILAS_PLANTILLA = 2000


def parsear_elemento(texto, ruta):
    t = texto.strip()
    if not t:
        raise ErrorSemantico("Hay un elemento vacío.", ruta=ruta)
    return int(t) if re.fullmatch(r"[+-]?\d+", t) else t


def parsear_dominio(texto):
    if not texto.strip():
        return []
    return [parsear_elemento(p, f"dominio[{i}]")
            for i, p in enumerate(texto.split(","))]


def _items(texto):
    return [p.strip() for p in re.split(r"[,;\n]+", texto) if p.strip()]


def parsear_firmas(texto, categoria):
    firmas = {}
    for item in _items(texto):
        m = re.fullmatch(rf"({_NOMBRE})\s*[/:]\s*(\d+)", item)
        if m is None:
            raise ErrorLenguaje(f"Se esperaba 'nombre/aridad', se recibió {item!r}.",
                                ruta=categoria)
        nombre, aridad = m.group(1), int(m.group(2))
        if nombre in firmas:
            raise ErrorLenguaje(f"Símbolo repetido: {nombre!r}.", ruta=categoria)
        firmas[nombre] = aridad
    return firmas


def construir_lenguaje(constantes_txt, funciones_txt, predicados_txt):
    return Lenguaje(constantes=_items(constantes_txt),
                    funciones=parsear_firmas(funciones_txt, "funciones"),
                    predicados=parsear_firmas(predicados_txt, "predicados"))


def _tupla(texto, ruta):
    t = texto.strip()
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1].strip()
    if not t:
        return ()
    return tuple(parsear_elemento(p, ruta) for p in t.split(","))


def parsear_tabla_funcion(texto, nombre):
    tabla = {}
    for n, linea in enumerate(texto.splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        ruta = f"funciones.{nombre} (línea {n})"
        partes = _FLECHA.split(linea, maxsplit=1)
        if len(partes) != 2:
            raise ErrorSemantico("Se esperaba 'entrada -> valor'.", ruta=ruta)
        if not partes[1].strip():
            raise ErrorSemantico("Falta el valor de salida.", ruta=ruta)
        clave = _tupla(partes[0], ruta)
        if clave in tabla:
            raise ErrorSemantico(f"Entrada repetida: {clave!r}.", ruta=ruta)
        tabla[clave] = parsear_elemento(partes[1], ruta)
    return tabla


def parsear_relacion(texto, nombre):
    filas = []
    for n, linea in enumerate(re.split(r"[\n;]+", texto), 1):
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            filas.append(_tupla(linea, f"relaciones.{nombre} (tupla {n})"))
    return filas


def plantilla_funcion(dominio, aridad):
    # Texto con todas las entradas de 𝒟ⁿ y la salida vacía, para completarla.
    if len(dominio) ** aridad > MAX_FILAS_PLANTILLA:
        raise ErrorSemantico(
            f"La tabla tendría {len(dominio) ** aridad} filas; escríbala a mano.",
            ruta="funciones")
    return "\n".join(", ".join(map(str, t)) + " -> "
                     for t in product(dominio, repeat=aridad))


def construir_interpretacion(lenguaje, dominio_txt, constantes_txt,
                             funciones_txt, relaciones_txt):
    dominio = parsear_dominio(dominio_txt)
    constantes = {}
    for c in sorted(lenguaje.constantes):
        valor = constantes_txt.get(c, "")
        if not valor.strip():
            raise ErrorSemantico(f"Falta el valor de la constante {c!r}.",
                                 ruta=f"constantes.{c}")
        constantes[c] = parsear_elemento(valor, f"constantes.{c}")
    funciones = {n: (a, parsear_tabla_funcion(funciones_txt.get(n, ""), n))
                 for n, a in lenguaje.funciones.items()}
    relaciones = {n: (a, parsear_relacion(relaciones_txt.get(n, ""), n))
                  for n, a in lenguaje.predicados.items()}
    return Interpretacion(dominio, constantes, funciones, relaciones,
                          lenguaje=lenguaje)


def construir_entorno(asignaciones):
    # Solo se leen las variables con valor escrito; las vacías quedan sin asignar.
    return Entorno({v: parsear_elemento(t, f"entorno.{v}")
                    for v, t in asignaciones.items() if t.strip()})


def ejemplo():
    # Mismos datos que interpretacion_ejemplo(), como texto para la interfaz.
    d = [1, 2, 3, 4]
    return {
        "lenguaje": ("a, b", "s/1, suma/2", "P/1, M/2"),
        "dominio": "1, 2, 3, 4",
        "constantes": {"a": "1", "b": "3"},
        "funciones": {
            "s": "\n".join(f"{x} -> {min(x + 1, 4)}" for x in d),
            "suma": "\n".join(f"{x}, {y} -> {min(x + y, 4)}" for x in d for y in d),
        },
        "relaciones": {
            "P": "2\n4",
            "M": "\n".join(f"({x}, {y})" for x in d for y in d if x < y),
        },
        "formula": "∀x ∃y M(x, y)",
    }
