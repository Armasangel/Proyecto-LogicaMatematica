"""Validación del AST completo, incluso las ramas que no se evaluarían."""

from errores import ErrorSemantico
from interpretacion import Entorno
from lenguaje import validar_nombre
from nodos import (Conjuncion, Constante, Disyuncion, Existe, Formula, Funcion,
                   Implicacion, Negacion, ParaTodo, Predicado, Variable, variables_libres)


def _error(nodo, mensaje):
    raise ErrorSemantico(mensaje, posicion=getattr(nodo, "posicion", None),
                        texto=getattr(nodo, "texto", None), ruta="formula")


def validar_termino(nodo, lenguaje):
    if isinstance(nodo, Variable):
        validar_nombre(nodo.nombre, "formula.variable")
        if nodo.nombre in lenguaje.simbolos:
            _error(nodo, f"{nodo.nombre!r} es un símbolo declarado, no una variable.")
    elif isinstance(nodo, Constante):
        if nodo.nombre not in lenguaje.constantes:
            _error(nodo, f"Constante no declarada: {nodo.nombre!r}.")
    elif isinstance(nodo, Funcion):
        _aplicacion(nodo, lenguaje.funciones, lenguaje, "Función")
    else:
        _error(nodo, "Se esperaba un término.")


def _aplicacion(nodo, declarados, lenguaje, categoria):
    if nodo.nombre not in declarados:
        _error(nodo, f"{categoria} no declarado/a: {nodo.nombre!r}.")
    aridad = declarados[nodo.nombre]
    if len(nodo.args) != aridad:
        _error(nodo, f"{nodo.nombre!r} espera {aridad} argumento(s), recibió {len(nodo.args)}.")
    for argumento in nodo.args:
        validar_termino(argumento, lenguaje)


def validar_formula(nodo, lenguaje):
    if not isinstance(nodo, Formula):
        _error(nodo, "Se esperaba una fórmula, no un término.")
    if isinstance(nodo, Predicado):
        _aplicacion(nodo, lenguaje.predicados, lenguaje, "Predicado")
    elif isinstance(nodo, Negacion):
        validar_formula(nodo.operando, lenguaje)
    elif isinstance(nodo, (Conjuncion, Disyuncion, Implicacion)):
        validar_formula(nodo.izq, lenguaje)
        validar_formula(nodo.der, lenguaje)
    elif isinstance(nodo, (ParaTodo, Existe)):
        validar_nombre(nodo.variable, "formula.cuantificador")
        if nodo.variable in lenguaje.simbolos:
            _error(nodo, "Un símbolo declarado no puede ligarse como variable.")
        validar_formula(nodo.cuerpo, lenguaje)
    else:
        _error(nodo, f"Tipo de fórmula desconocido: {type(nodo).__name__}.")
    return nodo


def validar_entrada(arbol, interpretacion, entorno=None):
    interpretacion.validar()
    validar_formula(arbol, interpretacion.lenguaje)
    sigma = entorno if isinstance(entorno, Entorno) else Entorno(entorno)
    faltantes = variables_libres(arbol) - sigma.keys()
    if faltantes:
        _error(arbol, "Variables libres sin asignación: " + ", ".join(sorted(faltantes)) + ".")
    sigma.validar(interpretacion.dominio, lenguaje=interpretacion.lenguaje)
    return sigma
