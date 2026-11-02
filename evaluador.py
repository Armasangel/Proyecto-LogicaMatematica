# Evaluador semántico de la lógica de primer orden con justificaciones.

# Contrato con el controlador:
#    Evaluador().evaluar(arbol) -> (valor: bool, explicacion: str)

from interpretacion import Entorno, ErrorSemantico, Interpretacion
from nodos import (
    Conjuncion, Constante, Disyuncion, Existe, Formula, Funcion, Implicacion,
    Negacion, ParaTodo, Predicado, Termino, Variable, variables_libres,
)


#  Juicio: resultado de evaluar una (sub)fórmula + su justificación

class Juicio:
    def __init__(self, valor, formula, razon, hijos=None,
                 testigo=None, contraejemplo=None, etiqueta=""):
        self.valor = valor
        self.formula = formula
        self.razon = razon
        self.hijos = hijos or []
        self.testigo = testigo              # elemento d de un ∃ verdadero
        self.contraejemplo = contraejemplo  # elemento d de un ∀ falso
        self.etiqueta = etiqueta            # p. ej. "x↦2" en hijos de cuantificadores

    def texto(self, max_hijos=10, prof_max=None):
        return "\n".join(self._lineas(0, max_hijos, prof_max))

    def _lineas(self, nivel, max_hijos, prof_max):
        sangria = "    " * nivel
        marca = f"[{self.etiqueta}] " if self.etiqueta else ""
        veredicto = "verdadera" if self.valor else "falsa"
        salida = [f"{sangria}{marca}{self.formula} es {veredicto}: {self.razon}"]
        if prof_max is not None and nivel >= prof_max:
            return salida
        for h in self.hijos[:max_hijos]:
            salida += h._lineas(nivel + 1, max_hijos, prof_max)
        resto = len(self.hijos) - max_hijos
        if resto > 0:
            salida.append(
                f"{sangria}    … y {resto} elementos más con el mismo resultado "
                f"(todos fueron comprobados)."
            )
        return salida


#  Evaluador

def _fmt_dominio(dominio):
    return "{" + ", ".join(map(str, dominio)) + "}"


def _fmt_tupla(t):
    return str(t[0]) if len(t) == 1 else "(" + ", ".join(map(str, t)) + ")"


class Evaluador:
    def __init__(self, interpretacion=None, entorno=None):
        self.interpretacion = interpretacion or interpretacion_ejemplo()
        self.entorno = entorno or Entorno()
        self.ultimo_juicio = None

    # términos 

    def evaluar_termino(self, termino, sigma=None):
        # Valor de un término en ℐ bajo σ (variables, constantes, f anidadas).
        sigma = self.entorno if sigma is None else sigma
        I = self.interpretacion
        if isinstance(termino, Variable):
            return sigma[termino.nombre]
        if isinstance(termino, Constante):
            return I.valor_constante(termino.nombre)
        if isinstance(termino, Funcion):
            args = tuple(self.evaluar_termino(a, sigma) for a in termino.args)
            return I.aplicar_funcion(termino.nombre, args)
        raise ErrorSemantico(f"Término desconocido: {termino!r}")

    # fórmulas 

    def evaluar_formula(self, formula, sigma=None):
        # Evalúa una fórmula bajo σ y devuelve un Juicio con la justificación.
        sigma = self.entorno if sigma is None else sigma
        sin_valor = sorted(v for v in variables_libres(formula) if v not in sigma)
        if sin_valor:
            raise ErrorSemantico(
                "Variables libres sin valor en el entorno: "
                + ", ".join(sin_valor)
                + ". Cuantifíquelas (∀/∃) o asígneles un valor."
            )
        return self._formula(formula, sigma)

    def evaluar(self, arbol):
        # Interfaz para el controlador: (valor, explicación en texto).
        if isinstance(arbol, Termino):
            raise ErrorSemantico("Se esperaba una fórmula, no un término.")
        juicio = self.evaluar_formula(arbol)
        self.ultimo_juicio = juicio
        return juicio.valor, juicio.texto()

    # recursión 

    def _formula(self, f, sigma):
        if isinstance(f, Predicado):
            return self._predicado(f, sigma)
        if isinstance(f, Negacion):
            return self._negacion(f, sigma)
        if isinstance(f, Conjuncion):
            return self._conjuncion(f, sigma)
        if isinstance(f, Disyuncion):
            return self._disyuncion(f, sigma)
        if isinstance(f, Implicacion):
            return self._implicacion(f, sigma)
        if isinstance(f, ParaTodo):
            return self._para_todo(f, sigma)
        if isinstance(f, Existe):
            return self._existe(f, sigma)
        raise ErrorSemantico(f"Fórmula desconocida: {f!r}")

    def _predicado(self, f, sigma):
        valores = tuple(self.evaluar_termino(a, sigma) for a in f.args)
        pertenece = self.interpretacion.satisface(f.nombre, valores)
        detalle = ", ".join(f"{a} = {v}" for a, v in zip(f.args, valores))
        rel = "∈" if pertenece else "∉"
        razon = f"{detalle}; {_fmt_tupla(valores)} {rel} {f.nombre}^ℐ"
        return Juicio(pertenece, f, razon)

    def _negacion(self, f, sigma):
        j = self._formula(f.operando, sigma)
        if j.valor:
            return Juicio(False, f, f"{f.operando} es verdadera", [j])
        return Juicio(True, f, f"{f.operando} es falsa", [j])

    def _conjuncion(self, f, sigma):
        izq = self._formula(f.izq, sigma)
        if not izq.valor:
            return Juicio(False, f, f"el primer operando ({f.izq}) es falso", [izq])
        der = self._formula(f.der, sigma)
        if not der.valor:
            return Juicio(
                False, f,
                f"el segundo operando ({f.der}) es falso (el primero es verdadero)",
                [der],
            )
        return Juicio(True, f, "ambos operandos son verdaderos", [izq, der])

    def _disyuncion(self, f, sigma):
        izq = self._formula(f.izq, sigma)
        if izq.valor:
            return Juicio(True, f, f"el primer operando ({f.izq}) es verdadero", [izq])
        der = self._formula(f.der, sigma)
        if der.valor:
            return Juicio(
                True, f,
                f"el segundo operando ({f.der}) es verdadero (el primero es falso)",
                [der],
            )
        return Juicio(False, f, "ambos operandos son falsos", [izq, der])

    def _implicacion(self, f, sigma):
        ant = self._formula(f.izq, sigma)
        if not ant.valor:
            return Juicio(
                True, f,
                f"el antecedente ({f.izq}) es falso, así que se cumple por vacuidad",
                [ant],
            )
        cons = self._formula(f.der, sigma)
        if cons.valor:
            return Juicio(
                True, f, f"el consecuente ({f.der}) es verdadero", [cons]
            )
        return Juicio(
            False, f,
            f"el antecedente ({f.izq}) es verdadero y el consecuente ({f.der}) es falso",
            [ant, cons],
        )

    # cuantificadores (σ[x↦d]) 

    def _para_todo(self, f, sigma):
        x, dom = f.variable, self.interpretacion.dominio
        hijos = []
        for d in dom:
            h = self._formula(f.cuerpo, sigma.modificado(x, d))
            h.etiqueta = f"{x}↦{d}"
            if not h.valor:
                return Juicio(
                    False, f,
                    f"contraejemplo {x} = {d}: con σ[{x}↦{d}], {f.cuerpo} es falsa",
                    [h], contraejemplo=d,
                )
            hijos.append(h)
        return Juicio(
            True, f,
            f"comprobación completa: los {len(dom)} elementos de "
            f"𝒟 = {_fmt_dominio(dom)} satisfacen {f.cuerpo}",
            hijos,
        )

    def _existe(self, f, sigma):
        x, dom = f.variable, self.interpretacion.dominio
        hijos = []
        for d in dom:
            h = self._formula(f.cuerpo, sigma.modificado(x, d))
            h.etiqueta = f"{x}↦{d}"
            if h.valor:
                return Juicio(
                    True, f,
                    f"testigo {x} = {d}: con σ[{x}↦{d}], {f.cuerpo} es verdadera",
                    [h], testigo=d,
                )
            hijos.append(h)
        return Juicio(
            False, f,
            f"comprobación completa: ninguno de los {len(dom)} elementos de "
            f"𝒟 = {_fmt_dominio(dom)} satisface {f.cuerpo}",
            hijos,
        )


#  Interpretación de ejemplo (la usa Evaluador() sin argumentos)

def interpretacion_ejemplo():
    # 𝒟 = {1,2,3,4}; a=1, b=3; s = sucesor (4↦4); P = pares; M = '<'.
    dominio = [1, 2, 3, 4]
    return Interpretacion(
        dominio,
        constantes={"a": 1, "b": 3},
        funciones={
            "s": (1, {(d,): min(d + 1, 4) for d in dominio}),
            "suma": (2, lambda x, y: min(x + y, 4)),
        },
        relaciones={
            "P": (1, {2, 4}),
            "M": (2, {(x, y) for x in dominio for y in dominio if x < y}),
        },
    )