# Estructuras de datos de una interpretación ℐ = (𝒟, {f^ℐ}, {P^ℐ}) y entornos σ.
from itertools import product


class ErrorSemantico(Exception):
    # Error al construir o evaluar con una interpretación.


class Entorno:
    # Asignación σ: variable ↦ elemento del dominio (inmutable en la práctica).

    def __init__(self, asignacion=None):
        self._a = dict(asignacion or {})

    def __getitem__(self, variable):
        if variable not in self._a:
            raise ErrorSemantico(
                f"La variable '{variable}' no tiene valor en el entorno."
            )
        return self._a[variable]

    def __contains__(self, variable):
        return variable in self._a

    def __iter__(self):
        return iter(self._a)

    def modificado(self, variable, elemento):
        # σ[x↦d]: copia de σ donde x vale d (σ original no cambia).
        nuevo = dict(self._a)
        nuevo[variable] = elemento
        return Entorno(nuevo)

    def __str__(self):
        if not self._a:
            return "σ = {}"
        return "σ = {" + ", ".join(f"{v}↦{d}" for v, d in self._a.items()) + "}"

def _como_tupla(clave):
    return clave if isinstance(clave, tuple) else (clave,)


class Interpretacion:
        # dominio:    iterable no vacío de elementos hashables (𝒟).
    # constantes: {nombre: elemento}                       (c^ℐ ∈ 𝒟)
    # funciones:  {nombre: (aridad, tabla_o_callable)}     (f^ℐ : 𝒟ⁿ → 𝒟)
                # tabla = {(d1,..,dn): valor}; debe ser total sobre 𝒟ⁿ.
    # relaciones: {nombre: (aridad, conjunto_o_callable)}  (P^ℐ ⊆ 𝒟ⁿ)
                # conjunto = {(d1,..,dn), ...}; para aridad 1 se aceptan escalares.

    def __init__(self, dominio, constantes=None, funciones=None, relaciones=None):
        dom = []
        for d in dominio:
            if d not in dom:
                dom.append(d)
        if not dom:
            raise ErrorSemantico("El dominio no puede ser vacío.")
        self.dominio = tuple(dom)

        self.constantes = {}
        for nombre, valor in (constantes or {}).items():
            self.agregar_constante(nombre, valor)

        self.funciones = {}
        for nombre, (aridad, impl) in (funciones or {}).items():
            self.agregar_funcion(nombre, aridad, impl)

        self.relaciones = {}
        for nombre, (aridad, impl) in (relaciones or {}).items():
            self.agregar_relacion(nombre, aridad, impl)

    # construcción

    def _en_dominio(self, elemento, contexto):
        if elemento not in self.dominio:
            raise ErrorSemantico(
                f"{contexto}: el valor {elemento!r} no pertenece al dominio."
            )

    def agregar_constante(self, nombre, valor):
        self._en_dominio(valor, f"Constante '{nombre}'")
        self.constantes[nombre] = valor

    def agregar_funcion(self, nombre, aridad, impl):
        if aridad < 1:
            raise ErrorSemantico(f"Función '{nombre}': la aridad debe ser ≥ 1.")
        if callable(impl):
            self.funciones[nombre] = (aridad, impl)
            return
        tabla = {_como_tupla(k): v for k, v in impl.items()}
        for args in product(self.dominio, repeat=aridad):
            if args not in tabla:
                raise ErrorSemantico(
                    f"Función '{nombre}': falta el valor en {args}; "
                    f"f^ℐ debe estar definida en todo 𝒟^{aridad}."
                )
        for args, v in tabla.items():
            self._en_dominio(v, f"Función '{nombre}' en {args}")
        self.funciones[nombre] = (aridad, tabla)

    def agregar_relacion(self, nombre, aridad, impl):
        if aridad < 1:
            raise ErrorSemantico(f"Predicado '{nombre}': la aridad debe ser ≥ 1.")
        if callable(impl):
            self.relaciones[nombre] = (aridad, impl)
            return
        tuplas = frozenset(_como_tupla(t) for t in impl)
        for t in tuplas:
            if len(t) != aridad:
                raise ErrorSemantico(
                    f"Predicado '{nombre}': la tupla {t} no tiene aridad {aridad}."
                )
            for d in t:
                self._en_dominio(d, f"Predicado '{nombre}' en {t}")
        self.relaciones[nombre] = (aridad, tuplas)

    # consulta 

    def valor_constante(self, nombre):
        if nombre not in self.constantes:
            raise ErrorSemantico(
                f"La interpretación no define la constante '{nombre}'."
            )
        return self.constantes[nombre]

    def aplicar_funcion(self, nombre, args):
        if nombre not in self.funciones:
            raise ErrorSemantico(
                f"La interpretación no define el símbolo funcional '{nombre}'."
            )
        aridad, impl = self.funciones[nombre]
        if len(args) != aridad:
            raise ErrorSemantico(
                f"'{nombre}' tiene aridad {aridad}, pero recibió {len(args)} argumentos."
            )
        if callable(impl):
            resultado = impl(*args)
            self._en_dominio(resultado, f"Función '{nombre}' en {args}")
            return resultado
        return impl[tuple(args)]

    def satisface(self, nombre, args):
        # ¿(d1,..,dn) ∈ P^ℐ?
        if nombre not in self.relaciones:
            raise ErrorSemantico(
                f"La interpretación no define el predicado '{nombre}'."
            )
        aridad, impl = self.relaciones[nombre]
        if len(args) != aridad:
            raise ErrorSemantico(
                f"'{nombre}' tiene aridad {aridad}, pero recibió {len(args)} argumentos."
            )
        if callable(impl):
            return bool(impl(*args))
        return tuple(args) in impl

    def describir(self):
        # Texto legible de la interpretación (para mostrar en la interfaz).
        lineas = ["𝒟 = {" + ", ".join(map(str, self.dominio)) + "}"]
        for c, v in self.constantes.items():
            lineas.append(f"{c}^ℐ = {v}")
        for f, (n, impl) in self.funciones.items():
            if callable(impl):
                lineas.append(f"{f}^ℐ : 𝒟^{n} → 𝒟 (calculada)")
            else:
                filas = ", ".join(
                    f"{'(' + ', '.join(map(str, k)) + ')' if n > 1 else k[0]}↦{v}"
                    for k, v in impl.items()
                )
                lineas.append(f"{f}^ℐ : {filas}")
        for p, (n, impl) in self.relaciones.items():
            if callable(impl):
                lineas.append(f"{p}^ℐ ⊆ 𝒟^{n} (calculada)")
            else:
                elems = ", ".join(
                    str(t[0]) if n == 1 else "(" + ", ".join(map(str, t)) + ")"
                    for t in sorted(impl, key=lambda t: [str(x) for x in t])
                )
                lineas.append(f"{p}^ℐ = {{{elems}}}")
        return "\n".join(lineas)