"""Interpretaciones finitas y entornos comprobados antes de evaluar."""

from collections.abc import Mapping
from itertools import product
from types import MappingProxyType

from errores import ErrorSemantico
from lenguaje import Lenguaje, validar_nombre


def _mapa(datos, ruta):
    if datos is None:
        return {}
    if not isinstance(datos, Mapping):
        raise ErrorSemantico("Se esperaba un diccionario.", ruta=ruta)
    return dict(datos)


def _coleccion(datos, ruta):
    if isinstance(datos, (str, bytes, Mapping)):
        raise ErrorSemantico("Se esperaba una colección de elementos.", ruta=ruta)
    try:
        return tuple(datos)
    except TypeError as exc:
        raise ErrorSemantico("Se esperaba una colección de elementos.", ruta=ruta) from exc


def _en_dominio(valor, dominio, ruta):
    try:
        valido = valor in dominio
    except TypeError:
        valido = False
    if not valido:
        raise ErrorSemantico(f"El valor {valor!r} no pertenece al dominio.", ruta=ruta)


def _tupla(valor, aridad, dominio, ruta):
    # Compatibilidad con el ejemplo existente P=(1, {2, 4}).
    if aridad == 1 and not isinstance(valor, (tuple, list)):
        valor = (valor,)
    if not isinstance(valor, (tuple, list)) or len(valor) != aridad:
        raise ErrorSemantico(f"Se esperaba una tupla de longitud {aridad}: {valor!r}.", ruta=ruta)
    salida = tuple(valor)
    for i, elemento in enumerate(salida):
        _en_dominio(elemento, dominio, f"{ruta}[{i}]")
    return salida


def _declaraciones(datos, ruta):
    salida = {}
    for nombre, entrada in _mapa(datos, ruta).items():
        if not isinstance(entrada, (tuple, list)) or len(entrada) != 2:
            raise ErrorSemantico("Se esperaba (aridad, tabla o relación).", ruta=f"{ruta}.{nombre}")
        aridad, contenido = entrada
        if type(aridad) is not int or aridad < 0:
            raise ErrorSemantico("La aridad debe ser un entero mayor o igual a cero.", ruta=f"{ruta}.{nombre}")
        salida[nombre] = (aridad, contenido)
    return salida


class Interpretacion:
    def __init__(self, dominio, constantes=None, funciones=None, relaciones=None, *, lenguaje=None):
        self.dominio = _coleccion(dominio, "dominio")
        if not self.dominio:
            raise ErrorSemantico("El dominio no puede estar vacío.", ruta="dominio")
        elementos = set()
        for i, elemento in enumerate(self.dominio):
            try:
                if elemento in elementos:
                    raise ErrorSemantico(f"Elemento duplicado: {elemento!r}.", ruta=f"dominio[{i}]")
                elementos.add(elemento)
            except TypeError as exc:
                raise ErrorSemantico("Los elementos del dominio deben ser hashables (por ejemplo, números o texto).",
                                     ruta=f"dominio[{i}]") from exc
        self._dominio = frozenset(elementos)
        constantes = _mapa(constantes, "constantes")
        funciones = _declaraciones(funciones, "funciones")
        relaciones = _declaraciones(relaciones, "relaciones")
        inferido = Lenguaje(constantes, {n: a for n, (a, _) in funciones.items()},
                            {n: a for n, (a, _) in relaciones.items()})
        self.lenguaje = inferido if lenguaje is None else lenguaje
        if not isinstance(self.lenguaje, Lenguaje):
            raise ErrorSemantico("Se esperaba un Lenguaje.", ruta="lenguaje")
        self._comprobar_firma(inferido)
        for nombre, valor in constantes.items():
            _en_dominio(valor, self._dominio, f"constantes.{nombre}")
        self.constantes = MappingProxyType(constantes)
        self.funciones = MappingProxyType({
            n: (a, MappingProxyType(self._funcion(n, a, tabla)))
            for n, (a, tabla) in funciones.items()
        })
        self.relaciones = MappingProxyType({
            n: (a, self._relacion(n, a, relacion))
            for n, (a, relacion) in relaciones.items()
        })

    def _comprobar_firma(self, interpretado):
        for categoria in ("constantes", "funciones", "predicados"):
            esperado = getattr(self.lenguaje, categoria)
            recibido = getattr(interpretado, categoria)
            faltantes = set(esperado) - set(recibido)
            sobrantes = set(recibido) - set(esperado)
            if faltantes:
                raise ErrorSemantico("Falta interpretación para: " + ", ".join(sorted(faltantes)) + ".", ruta=categoria)
            if sobrantes:
                raise ErrorSemantico("Símbolos no declarados: " + ", ".join(sorted(sobrantes)) + ".", ruta=categoria)
            if categoria != "constantes":
                for nombre, aridad in esperado.items():
                    if recibido[nombre] != aridad:
                        raise ErrorSemantico(f"Aridad incorrecta para {nombre!r}: se esperaba {aridad}.", ruta=f"{categoria}.{nombre}")

    def _funcion(self, nombre, aridad, datos):
        ruta = f"funciones.{nombre}"
        tabla = {}
        if callable(datos):
            # Se comprueban TODAS las entradas y se congela el resultado.
            # No se vuelve a ejecutar una función externa durante la evaluación.
            for entrada in product(self.dominio, repeat=aridad):
                try:
                    valor = datos(*entrada)
                except Exception as exc:
                    raise ErrorSemantico(f"La función no está definida en {entrada!r}: {exc}.", ruta=ruta) from exc
                _en_dominio(valor, self._dominio, f"{ruta}[{entrada!r}]")
                tabla[entrada] = valor
            return tabla
        if not isinstance(datos, Mapping):
            raise ErrorSemantico("La función debe ser una tabla o un callable.", ruta=ruta)
        if not datos:
            raise ErrorSemantico("La función no puede estar vacía.", ruta=ruta)
        for entrada, valor in datos.items():
            clave = _tupla(entrada, aridad, self._dominio, ruta)
            if clave in tabla:
                raise ErrorSemantico(f"Entrada duplicada de la función: {clave!r}.", ruta=ruta)
            _en_dominio(valor, self._dominio, f"{ruta}[{clave!r}]")
            tabla[clave] = valor
        for entrada in product(self.dominio, repeat=aridad):
            if entrada not in tabla:
                raise ErrorSemantico(f"La función no es total: falta la entrada {entrada!r}.", ruta=ruta)
        return tabla

    def _relacion(self, nombre, aridad, datos):
        ruta = f"relaciones.{nombre}"
        filas = _coleccion(datos, ruta)
        if not filas:
            raise ErrorSemantico("La relación no puede estar vacía.", ruta=ruta)
        return frozenset(_tupla(fila, aridad, self._dominio, f"{ruta}[{i}]")
                         for i, fila in enumerate(filas))

    def validar(self):
        """Revisa también cambios posteriores en los atributos públicos."""
        revisada = Interpretacion(self.dominio, self.constantes, self.funciones,
                                  self.relaciones, lenguaje=self.lenguaje)
        self.__dict__.update(revisada.__dict__)
        return self

    def valor_constante(self, nombre):
        if nombre not in self.constantes:
            raise ErrorSemantico(f"Constante no declarada: {nombre!r}.", ruta="constantes")
        return self.constantes[nombre]

    def aplicar_funcion(self, nombre, args):
        if nombre not in self.funciones:
            raise ErrorSemantico(f"Función no declarada: {nombre!r}.", ruta="funciones")
        aridad, tabla = self.funciones[nombre]
        clave = _tupla(args, aridad, self._dominio, f"funciones.{nombre}")
        if clave not in tabla:
            raise ErrorSemantico(f"La función no está definida en {clave!r}.", ruta=f"funciones.{nombre}")
        return tabla[clave]

    def satisface(self, nombre, args):
        if nombre not in self.relaciones:
            raise ErrorSemantico(f"Predicado no declarado: {nombre!r}.", ruta="relaciones")
        aridad, relacion = self.relaciones[nombre]
        return _tupla(args, aridad, self._dominio, f"relaciones.{nombre}") in relacion


class Entorno(Mapping):
    def __init__(self, asignaciones=None):
        valores = _mapa(asignaciones, "entorno")
        for nombre in valores:
            validar_nombre(nombre, "entorno")
        self._valores = MappingProxyType(valores)

    def __getitem__(self, nombre):
        if nombre not in self._valores:
            raise ErrorSemantico(f"Falta una asignación para la variable {nombre!r}.", ruta=f"entorno.{nombre}")
        return self._valores[nombre]

    def __iter__(self):
        return iter(self._valores)

    def __len__(self):
        return len(self._valores)

    def __contains__(self, nombre):
        return nombre in self._valores

    def modificado(self, nombre, valor):
        return Entorno({**self._valores, nombre: valor})

    def validar(self, dominio, requeridas=(), *, lenguaje=None):
        elementos = frozenset(dominio)
        for nombre, valor in self.items():
            if lenguaje is not None and nombre in lenguaje.simbolos:
                raise ErrorSemantico(f"{nombre!r} es un símbolo del lenguaje, no una variable.", ruta=f"entorno.{nombre}")
            _en_dominio(valor, elementos, f"entorno.{nombre}")
        faltantes = set(requeridas) - self.keys()
        if faltantes:
            raise ErrorSemantico("Variables libres sin asignación: " + ", ".join(sorted(faltantes)) + ".", ruta="entorno")
        return self
