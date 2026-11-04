"""AST compatible con el evaluador de Persona 1."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Nodo:
    posicion: int | None = field(default=None, kw_only=True, compare=False, repr=False)
    texto: str | None = field(default=None, kw_only=True, compare=False, repr=False)


class Termino(Nodo):
    pass


class Formula(Nodo):
    pass


@dataclass(frozen=True)
class Variable(Termino):
    nombre: str

    def __str__(self):
        return self.nombre


@dataclass(frozen=True)
class Constante(Termino):
    nombre: str

    def __str__(self):
        return self.nombre


@dataclass(frozen=True)
class Funcion(Termino):
    nombre: str
    args: tuple

    def __post_init__(self):
        object.__setattr__(self, "args", tuple(self.args))

    def __str__(self):
        return f"{self.nombre}({', '.join(map(str, self.args))})"


@dataclass(frozen=True)
class Predicado(Formula):
    nombre: str
    args: tuple

    def __post_init__(self):
        object.__setattr__(self, "args", tuple(self.args))

    def __str__(self):
        return f"{self.nombre}({', '.join(map(str, self.args))})"


@dataclass(frozen=True)
class Negacion(Formula):
    operando: Formula

    def __str__(self):
        return f"¬{self.operando}"


@dataclass(frozen=True)
class Binaria(Formula):
    izq: Formula
    der: Formula

    def __str__(self):
        return f"({self.izq} {self.simbolo} {self.der})"


class Conjuncion(Binaria):
    simbolo = "∧"


class Disyuncion(Binaria):
    simbolo = "∨"


class Implicacion(Binaria):
    simbolo = "→"


@dataclass(frozen=True)
class Cuantificador(Formula):
    variable: str
    cuerpo: Formula

    def __str__(self):
        return f"{self.simbolo}{self.variable}({self.cuerpo})"


class ParaTodo(Cuantificador):
    simbolo = "∀"


class Existe(Cuantificador):
    simbolo = "∃"


def variables_libres(nodo):
    if isinstance(nodo, Variable):
        return {nodo.nombre}
    if isinstance(nodo, Constante):
        return set()
    if isinstance(nodo, (Funcion, Predicado)):
        return set().union(*(variables_libres(a) for a in nodo.args))
    if isinstance(nodo, Negacion):
        return variables_libres(nodo.operando)
    if isinstance(nodo, Binaria):
        return variables_libres(nodo.izq) | variables_libres(nodo.der)
    if isinstance(nodo, Cuantificador):
        return variables_libres(nodo.cuerpo) - {nodo.variable}
    raise TypeError(f"Nodo desconocido: {nodo!r}")


def variables_ligadas(nodo):
    """Nombres introducidos por cuantificadores, incluidos los vacuos."""
    if isinstance(nodo, (Variable, Constante)):
        return set()
    if isinstance(nodo, (Funcion, Predicado)):
        return set().union(*(variables_ligadas(a) for a in nodo.args))
    if isinstance(nodo, Negacion):
        return variables_ligadas(nodo.operando)
    if isinstance(nodo, Binaria):
        return variables_ligadas(nodo.izq) | variables_ligadas(nodo.der)
    if isinstance(nodo, Cuantificador):
        return {nodo.variable} | variables_ligadas(nodo.cuerpo)
    raise TypeError(f"Nodo desconocido: {nodo!r}")
