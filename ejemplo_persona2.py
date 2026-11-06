"""Demostración sin modificar la interfaz ni el evaluador originales."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from analizador_sintactico import AnalizadorSintactico
from errores import ErrorValidacion
from evaluador import Evaluador
from interpretacion import Interpretacion
from lenguaje import Lenguaje
from nodos import variables_libres, variables_ligadas


def main():
    lenguaje = Lenguaje(constantes=["c"], funciones={"s": 1}, predicados={"P": 1})
    interpretacion = Interpretacion(
        dominio=[1, 2, 3],
        constantes={"c": 1},
        funciones={"s": (1, {(1,): 2, (2,): 3, (3,): 3})},
        relaciones={"P": (1, {(2,), (3,)})},
        lenguaje=lenguaje,
    )
    parser = AnalizadorSintactico(lenguaje)
    for texto, entorno in [
        ("∀x (P(s(x)))", {}),
        ("∃x P(x)", {}),
        ("P(x) ∧ P(s(c))", {"x": 2}),
        ("P(x)", {}),  # Error: se debe pedir un entorno antes de evaluar.
        ("P(s(c, c))", {}),  # Error de aridad con posición.
    ]:
        print(f"\nFórmula: {texto}")
        try:
            arbol = parser.analizar(texto)
            print("AST:", arbol)
            print("Libres:", sorted(variables_libres(arbol)))
            print("Ligadas:", sorted(variables_ligadas(arbol)))
            valor, explicacion = Evaluador(interpretacion, entorno).evaluar(arbol)
            print("Resultado:", "Verdadero" if valor else "Falso")
            print(explicacion)
        except ErrorValidacion as error:
            print("Error:", error)


if __name__ == "__main__":
    main()
