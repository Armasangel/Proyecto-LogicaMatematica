"""Parser descendente: prefijos > conjunción > disyunción > implicación."""

from errores import ErrorSintaxis
from lenguaje import Lenguaje, lenguaje_ejemplo
from nodos import (Conjuncion, Constante, Disyuncion, Existe, Funcion,
                   Implicacion, Negacion, ParaTodo, Predicado, Variable,
                   variables_libres, variables_ligadas)
from tokenizer import tokenizar


class AnalizadorSintactico:
    def __init__(self, lenguaje=None):
        self.lenguaje = lenguaje_ejemplo() if lenguaje is None else lenguaje
        if not isinstance(self.lenguaje, Lenguaje):
            raise TypeError("Se esperaba un Lenguaje.")

    def analizar(self, texto):
        # Estado por llamada: analizar una segunda fórmula no altera el primer AST.
        return _Parser(texto, self.lenguaje).analizar()

    def analizar_con_variables(self, texto):
        arbol = self.analizar(texto)
        return arbol, variables_libres(arbol), variables_ligadas(arbol)


class _Parser:
    def __init__(self, texto, lenguaje):
        self.tokens = tokenizar(texto)
        self.texto, self.lenguaje, self.i = texto, lenguaje, 0

    @property
    def actual(self):
        return self.tokens[self.i]

    def error(self, mensaje, token=None):
        token = self.actual if token is None else token
        raise ErrorSintaxis(mensaje, posicion=token.posicion, texto=self.texto)

    def tomar(self, tipo):
        if self.actual.tipo == tipo:
            token = self.actual
            self.i += 1
            return token
        return None

    def exigir(self, tipo, mensaje):
        token = self.tomar(tipo)
        if token is None:
            self.error(mensaje)
        return token

    def crear(self, clase, token, *args):
        return clase(*args, posicion=token.posicion, texto=self.texto)

    def analizar(self):
        if self.actual.tipo == "FIN":
            self.error("La fórmula está vacía.")
        try:
            arbol = self.implicacion()
        except RecursionError:
            self.error("La fórmula supera la profundidad de anidamiento admitida.")
        if self.actual.tipo != "FIN":
            self.error(f"Token inesperado: {self.actual.valor!r}; falta un conectivo o sobra un paréntesis.")
        return arbol

    def implicacion(self):
        izq = self.disyuncion()
        token = self.tomar("IMPLICA")
        if token:
            return self.crear(Implicacion, token, izq, self.implicacion())
        return izq

    def disyuncion(self):
        izq = self.conjuncion()
        while (token := self.tomar("O")) is not None:
            izq = self.crear(Disyuncion, token, izq, self.conjuncion())
        return izq

    def conjuncion(self):
        izq = self.prefijo()
        while (token := self.tomar("Y")) is not None:
            izq = self.crear(Conjuncion, token, izq, self.prefijo())
        return izq

    def prefijo(self):
        if (token := self.tomar("NO")) is not None:
            return self.crear(Negacion, token, self.prefijo())
        if self.actual.tipo in {"TODOS", "EXISTE"}:
            token = self.actual
            self.i += 1
            variable = self.exigir("ID", "Se esperaba una variable después del cuantificador.")
            if variable.valor in self.lenguaje.simbolos:
                self.error(f"{variable.valor!r} es un símbolo declarado y no puede ligarse como variable.", variable)
            self.tomar("PUNTO")
            clase = ParaTodo if token.tipo == "TODOS" else Existe
            return self.crear(clase, token, variable.valor, self.prefijo())
        if self.tomar("ABRE"):
            formula = self.implicacion()
            self.exigir("CIERRA", "Falta ')' para cerrar la fórmula.")
            return formula
        return self.atomo()

    def argumentos(self):
        self.exigir("ABRE", "Se esperaba '(' después del símbolo.")
        args = []
        if self.tomar("CIERRA"):
            return tuple(args)
        args.append(self.termino())
        while self.tomar("COMA"):
            args.append(self.termino())
        self.exigir("CIERRA", "Se esperaba ',' o ')' después del término.")
        return tuple(args)

    def comprobar_aridad(self, token, args, aridad):
        if len(args) != aridad:
            self.error(f"{token.valor!r} espera {aridad} argumento(s), recibió {len(args)}.", token)

    def atomo(self):
        token = self.exigir("ID", "Se esperaba un predicado, una negación, un cuantificador o '('.")
        if token.valor not in self.lenguaje.predicados:
            self.error(f"Predicado no declarado: {token.valor!r}.", token)
        aridad = self.lenguaje.predicados[token.valor]
        args = () if aridad == 0 and self.actual.tipo != "ABRE" else self.argumentos()
        self.comprobar_aridad(token, args, aridad)
        return self.crear(Predicado, token, token.valor, args)

    def termino(self):
        token = self.exigir("ID", "Se esperaba un término (variable, constante o función).")
        nombre = token.valor
        if nombre in self.lenguaje.funciones:
            aridad = self.lenguaje.funciones[nombre]
            args = () if aridad == 0 and self.actual.tipo != "ABRE" else self.argumentos()
            self.comprobar_aridad(token, args, aridad)
            return self.crear(Funcion, token, nombre, args)
        if nombre in self.lenguaje.constantes:
            if self.actual.tipo == "ABRE":
                self.error(f"La constante {nombre!r} no recibe argumentos.", token)
            return self.crear(Constante, token, nombre)
        if nombre in self.lenguaje.predicados:
            self.error(f"El predicado {nombre!r} no puede usarse como término.", token)
        if self.actual.tipo == "ABRE":
            self.error(f"Función no declarada: {nombre!r}.", token)
        # Los identificadores de términos no declarados son variables libres.
        return self.crear(Variable, token, nombre)
