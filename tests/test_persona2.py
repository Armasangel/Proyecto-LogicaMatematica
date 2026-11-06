"""Ejecutar desde la raíz: python -B -m unittest discover -s tests -v"""

import importlib.util
from pathlib import Path
import sys
import unittest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from analizador_sintactico import AnalizadorSintactico
from controlador import Controlador
from errores import ErrorLenguaje, ErrorSemantico, ErrorSintaxis, ErrorValidacion
from evaluador import Evaluador, interpretacion_ejemplo
from interpretacion import Entorno, Interpretacion
from lenguaje import Lenguaje
from nodos import (Binaria, Conjuncion, Constante, Disyuncion, Existe, Funcion,
                   Implicacion, Negacion, ParaTodo, Predicado, Variable,
                   variables_libres, variables_ligadas)
from tokenizer import tokenizar
from validacion import validar_entrada


class SintaxisTests(unittest.TestCase):
    def setUp(self):
        self.parser = AnalizadorSintactico()

    def test_tokens_posiciones(self):
        tokens = tokenizar("  ¬P(x) -> P(a)")
        self.assertEqual([(t.tipo, t.posicion) for t in tokens[:3]],
                         [("NO", 2), ("ID", 3), ("ABRE", 4)])
        self.assertEqual(tokens[-1].tipo, "FIN")

    def test_precedencia_completa(self):
        f = self.parser.analizar("¬P(a) ∧ P(b) ∨ P(a) → P(b)")
        self.assertIsInstance(f, Implicacion)
        self.assertIsInstance(f.izq, Disyuncion)
        self.assertIsInstance(f.izq.izq, Conjuncion)
        self.assertIsInstance(f.izq.izq.izq, Negacion)

    def test_implicacion_asociativa_derecha(self):
        f = self.parser.analizar("P(a) → P(b) → P(a)")
        self.assertIsInstance(f.der, Implicacion)
        self.assertIsInstance(f.izq, Predicado)

    def test_conjuncion_y_disyuncion_asociativas_izquierda(self):
        for simbolo, clase in [("∧", Conjuncion), ("∨", Disyuncion)]:
            with self.subTest(simbolo=simbolo):
                f = self.parser.analizar(f"P(a) {simbolo} P(b) {simbolo} P(a)")
                self.assertIsInstance(f.izq, clase)
                self.assertIsInstance(f.der, Predicado)

    def test_parentesis_cambian_agrupacion(self):
        f = self.parser.analizar("(P(a) → P(b)) → P(a)")
        self.assertIsInstance(f.izq, Implicacion)

    def test_funciones_anidadas(self):
        f = self.parser.analizar("M(s(s(x)), suma(a, b))")
        self.assertIsInstance(f.args[0].args[0], Funcion)
        self.assertEqual(variables_libres(f), {"x"})

    def test_cuantificadores_anidados(self):
        f = self.parser.analizar("∀x(∃y(M(x, y) ∨ P(s(x))))")
        self.assertIsInstance(f, ParaTodo)
        self.assertIsInstance(f.cuerpo, Existe)
        self.assertEqual(variables_libres(f), set())
        self.assertEqual(variables_ligadas(f), {"x", "y"})

    def test_alcance_cuantificador_es_prefijo(self):
        f = self.parser.analizar("∀x P(x) → P(x)")
        self.assertIsInstance(f, Implicacion)
        self.assertEqual(variables_libres(f), {"x"})
        self.assertEqual(variables_ligadas(f), {"x"})

    def test_sombreado_y_variable_libre_en_otra_rama(self):
        f, libres, ligadas = self.parser.analizar_con_variables("∀x(P(x) ∧ ∃x M(x, y)) ∨ P(x)")
        self.assertEqual(libres, {"x", "y"})
        self.assertEqual(ligadas, {"x"})
        self.assertEqual(variables_libres(f), libres)

    def test_cuantificador_vacuo(self):
        f = self.parser.analizar("∀x P(a)")
        self.assertEqual(variables_libres(f), set())
        self.assertEqual(variables_ligadas(f), {"x"})

    def test_alias_ascii(self):
        self.assertEqual(self.parser.analizar("forall x. (~P(x) | P(a)) -> exists y P(y)"),
                         self.parser.analizar("∀x(¬P(x) ∨ P(a)) → ∃y P(y)"))

    def test_firma_personalizada_y_aridad_cero(self):
        parser = AnalizadorSintactico(Lenguaje(["c"], {"f": 2, "g": 0}, {"R": 2, "Q": 0}))
        f = parser.analizar("R(f(c, x), g()) ∧ Q")
        self.assertEqual(variables_libres(f), {"x"})
        self.assertEqual(str(f.der), "Q()")
        self.assertEqual(parser.analizar("Q"), parser.analizar("Q()"))

    def test_entradas_invalidas_no_producen_ast(self):
        casos = ["", "   ", "P(a", "P(a))", "(P(a)", "P(a) P(b)",
                 "P(a) →", "∧ P(a)", "Q(a)", "P(f(a))", "P(s(a, b))",
                 "M(a)", "P()", "P(a, b)", "P(a,)", "P(,a)",
                 "P(P(a))", "P(a())", "∀a P(a)", "∀ P(a)", "∀x", "P(a) $ P(b)"]
        for texto in casos:
            with self.subTest(texto=texto), self.assertRaises(ErrorSintaxis):
                self.parser.analizar(texto)

    def test_linea_columna_y_caret(self):
        with self.assertRaises(ErrorSintaxis) as cm:
            self.parser.analizar("P(a) ∧\n Q(a)")
        self.assertEqual((cm.exception.linea, cm.exception.columna), (2, 2))
        self.assertEqual(cm.exception.posicion, 8)
        self.assertIn("^", str(cm.exception))

    def test_parser_reutilizable(self):
        primero = self.parser.analizar("P(x)")
        self.parser.analizar("P(a)")
        self.assertEqual(variables_libres(primero), {"x"})


class LenguajeTests(unittest.TestCase):
    def test_nombres_y_aridades_invalidas(self):
        casos = [lambda: Lenguaje(funciones={"f": -1}),
                 lambda: Lenguaje(predicados={"P": True}),
                 lambda: Lenguaje(predicados={"P": 1.5}),
                 lambda: Lenguaje(constantes=["a", "a"]),
                 lambda: Lenguaje(constantes="abc"),
                 lambda: Lenguaje(funciones={"a": 1}, constantes=["a"]),
                 lambda: Lenguaje(funciones={"P": 1}, predicados={"P": 1}),
                 lambda: Lenguaje(predicados={"P mala": 1}),
                 lambda: Lenguaje(predicados={"forall": 1})]
        for i, caso in enumerate(casos):
            with self.subTest(i=i), self.assertRaises(ErrorLenguaje):
                caso()

    def test_firma_no_comparte_diccionarios_mutables(self):
        datos = {"f": 1}
        lenguaje = Lenguaje(funciones=datos)
        datos["f"] = 2
        self.assertEqual(lenguaje.funciones["f"], 1)
        with self.assertRaises(TypeError):
            lenguaje.funciones["f"] = 2


class InterpretacionTests(unittest.TestCase):
    def test_dominio_invalido(self):
        for dominio in [[], [1, 1], [1, True], [[1]], "12", None]:
            with self.subTest(dominio=dominio), self.assertRaises(ErrorSemantico):
                Interpretacion(dominio)

    def test_constante_fuera_del_dominio(self):
        with self.assertRaises(ErrorSemantico):
            Interpretacion([1], constantes={"a": 2})

    def test_funcion_vacia_parcial_y_fuera_del_dominio(self):
        for tabla in [{}, {(1,): 1}, {(1,): 1, (2,): 3}, {(1,): 1, (3,): 1},
                      {(1, 2): 1}, {1: 1, (1,): 2, 2: 2}]:
            with self.subTest(tabla=tabla), self.assertRaises(ErrorSemantico):
                Interpretacion([1, 2], funciones={"f": (1, tabla)})

    def test_funcion_binaria_total(self):
        tabla = {(x, y): max(x, y) for x in [1, 2] for y in [1, 2]}
        i = Interpretacion([1, 2], funciones={"f": (2, tabla)})
        self.assertEqual(i.aplicar_funcion("f", (1, 2)), 2)
        tabla.pop((1, 1))
        self.assertEqual(i.aplicar_funcion("f", (1, 1)), 1)

    def test_callable_se_comprueba_completo_y_se_congela(self):
        llamadas = []

        def f(x):
            llamadas.append(x)
            return x

        i = Interpretacion([1, 2], funciones={"f": (1, f)})
        self.assertEqual(llamadas, [1, 2])
        i.aplicar_funcion("f", (1,))
        i.validar()
        self.assertEqual(llamadas, [1, 2])

    def test_callable_parcial_o_resultado_invalido(self):
        for f in [lambda x: {1: 1}[x], lambda x: 3 if x == 2 else 1]:
            with self.subTest(f=f), self.assertRaises(ErrorSemantico):
                Interpretacion([1, 2], funciones={"f": (1, f)})

    def test_relaciones_invalidas(self):
        for filas in [[], [(1,)], [(1, 2, 1)], [(1, 3)], [1]]:
            with self.subTest(filas=filas), self.assertRaises(ErrorSemantico):
                Interpretacion([1, 2], relaciones={"R": (2, filas)})

    def test_relacion_unaria_en_formato_del_evaluador(self):
        i = Interpretacion([1, 2], relaciones={"P": (1, {2})})
        self.assertTrue(i.satisface("P", (2,)))
        self.assertFalse(i.satisface("P", (1,)))

    def test_simbolos_de_aridad_cero(self):
        i = Interpretacion([1], funciones={"c": (0, {(): 1})}, relaciones={"Q": (0, {()})})
        self.assertEqual(i.aplicar_funcion("c", ()), 1)
        self.assertTrue(i.satisface("Q", ()))

    def test_declaracion_incompleta_sobrante_o_aridad_distinta(self):
        lenguaje = Lenguaje(funciones={"f": 1}, predicados={"P": 1})
        casos = [dict(),
                 dict(funciones={"f": (1, {(1,): 1})}),
                 dict(funciones={"f": (0, {(): 1})}, relaciones={"P": (1, {1})}),
                 dict(funciones={"f": (1, {(1,): 1})}, relaciones={"P": (1, {1}), "Q": (1, {1})})]
        for caso in casos:
            with self.subTest(caso=caso), self.assertRaises(ErrorSemantico):
                Interpretacion([1], lenguaje=lenguaje, **caso)

    def test_estructura_de_interpretacion_invalida(self):
        casos = [dict(funciones={"f": 1}), dict(funciones={"f": (-1, {})}),
                 dict(relaciones={"P": (True, {1})}), dict(constantes=[]),
                 dict(funciones={"f": (1, [])}), dict(relaciones={"P": (1, "1")})]
        for caso in casos:
            with self.subTest(caso=caso), self.assertRaises(ErrorValidacion):
                Interpretacion([1], **caso)

    def test_metodos_directos_validan(self):
        i = interpretacion_ejemplo()
        for operacion in [lambda: i.valor_constante("c"),
                          lambda: i.aplicar_funcion("f", (1,)),
                          lambda: i.aplicar_funcion("s", (1, 2)),
                          lambda: i.satisface("Q", (1,)),
                          lambda: i.satisface("P", (9,))]:
            with self.subTest(operacion=operacion), self.assertRaises(ErrorSemantico):
                operacion()

    def test_error_datos_indica_campo(self):
        with self.assertRaises(ErrorSemantico) as cm:
            Interpretacion([1, 2], funciones={"f": (1, {(1,): 1})})
        self.assertEqual(cm.exception.ruta, "funciones.f")
        self.assertIn("(2,)", str(cm.exception))


class EntornoTests(unittest.TestCase):
    def test_faltante_e_invalido(self):
        for entorno in [{}, {"x": 3}, {"x": []}]:
            with self.subTest(entorno=entorno), self.assertRaises(ErrorSemantico):
                Entorno(entorno).validar([1, 2], {"x"})

    def test_asignacion_extra_invalida_se_rechaza(self):
        with self.assertRaises(ErrorSemantico):
            Entorno({"x": 1, "y": 3}).validar([1, 2], {"x"})

    def test_modificado_no_cambia_entorno_original(self):
        original = Entorno({"x": 1})
        nuevo = original.modificado("x", 2)
        self.assertEqual(original["x"], 1)
        self.assertEqual(nuevo["x"], 2)
        self.assertIn("x", original)
        self.assertNotIn("z", original)

    def test_asignacion_a_simbolo_declarado_se_rechaza(self):
        with self.assertRaises(ErrorSemantico):
            Entorno({"a": 1}).validar([1], lenguaje=Lenguaje(["a"]))


class IntegracionTests(unittest.TestCase):
    def setUp(self):
        self.parser = AnalizadorSintactico()

    def test_controlador_existente_funciona_sin_editarlo(self):
        controlador = Controlador()
        for texto, esperado in [("P(a)", False), ("P(s(a))", True),
                                ("∀x P(x)", False), ("∃x P(x)", True),
                                ("∀x (P(x) ∨ ¬P(x))", True),
                                ("∃x M(x, a)", False),
                                ("P(a) → P(x)", None), ("P(x)", None),
                                ("Q(a)", None), ("P(a, b)", None), ("", None)]:
            with self.subTest(texto=texto):
                resultado = controlador.evaluar(texto)
                self.assertIs(resultado.valor, esperado)
                self.assertEqual(resultado.es_error, esperado is None)

    def test_formula_abierta_y_entorno_configurable(self):
        controlador = Controlador()
        controlador.evaluador = Evaluador(entorno={"x": 2})
        resultado = controlador.evaluar("P(x)")
        self.assertFalse(resultado.es_error)
        self.assertTrue(resultado.valor)

    def test_lenguaje_personalizado_en_controlador(self):
        lenguaje = Lenguaje(["c"], {"f": 1}, {"R": 1})
        i = Interpretacion(["rojo", "azul"], {"c": "rojo"},
                           {"f": (1, {("rojo",): "azul", ("azul",): "azul"})},
                           {"R": (1, {"azul"})}, lenguaje=lenguaje)
        controlador = Controlador()
        controlador.analizador = AnalizadorSintactico(lenguaje)
        controlador.evaluador = Evaluador(i)
        self.assertTrue(controlador.evaluar("R(f(c))").valor)

    def test_justificaciones_testigo_contraejemplo_comprobacion(self):
        controlador = Controlador()
        for texto, palabra in [("∃x P(x)", "testigo"), ("∀x P(x)", "contraejemplo"),
                               ("∀x (P(x) ∨ ¬P(x))", "comprobación completa"),
                               ("∃x M(x, a)", "comprobación completa")]:
            with self.subTest(texto=texto):
                resultado = controlador.evaluar(texto)
                self.assertFalse(resultado.es_error)
                self.assertIn(palabra, resultado.explicacion)

    def test_ast_invalido_en_rama_omitida_no_recibe_valor(self):
        for arbol in [Disyuncion(Predicado("P", (Constante("b"),)), Predicado("Q", ())),
                      Implicacion(Predicado("P", (Constante("a"),)), Predicado("P", ())),
                      Disyuncion(Predicado("P", (Funcion("s", (Constante("a"),)),)),
                                 Binaria(Predicado("P", ()), Predicado("P", ())))]:
            with self.subTest(arbol=arbol), self.assertRaises(ErrorSemantico):
                Evaluador().evaluar(arbol)

    def test_entorno_invalido_no_se_oculta_con_cortocircuito(self):
        arbol = self.parser.analizar("P(s(a)) ∨ P(x)")
        for entorno in [{}, {"x": 9}, {"x": 2, "z": 9}]:
            with self.subTest(entorno=entorno), self.assertRaises(ErrorSemantico):
                Evaluador(entorno=entorno).evaluar(arbol)

    def test_sombreado_no_modifica_asignacion_externa(self):
        e = Evaluador(entorno={"x": 2})
        self.assertTrue(e.evaluar(self.parser.analizar("∃x P(x) ∧ P(x)"))[0])
        self.assertEqual(e.entorno["x"], 2)

    def test_tipos_de_terminos_invalidos_no_reciben_valor(self):
        for arbol in [Variable("x"), Predicado("P", (Predicado("P", ()),)),
                      Predicado("P", (Constante("c"),)),
                      Predicado("P", (Variable("a"),)),
                      ParaTodo("a", Predicado("P", (Constante("a"),)))]:
            with self.subTest(arbol=arbol), self.assertRaises(ErrorSemantico):
                Evaluador().evaluar(arbol)

    def test_error_no_deja_juicio_previo(self):
        e = Evaluador()
        e.evaluar(self.parser.analizar("P(a)"))
        self.assertIsNotNone(e.ultimo_juicio)
        with self.assertRaises(ErrorSemantico):
            e.evaluar(self.parser.analizar("P(x)"))
        self.assertIsNone(e.ultimo_juicio)

    def test_validacion_previa_detecta_cambio_en_interpretacion(self):
        i = interpretacion_ejemplo()
        i.dominio = ()
        with self.assertRaises(ErrorSemantico):
            validar_entrada(self.parser.analizar("P(a)"), i)

    def test_cambio_publico_valido_se_normaliza_antes_de_evaluar(self):
        i = Interpretacion([1, 2], relaciones={"P": (1, {1})})
        i.relaciones = {"P": (1, {2})}
        parser = AnalizadorSintactico(i.lenguaje)
        self.assertTrue(Evaluador(i, {"x": 2}).evaluar(parser.analizar("P(x)"))[0])

    def test_evaluador_original_sigue_compatible(self):
        spec = importlib.util.spec_from_file_location("_original_prueba", RAIZ / "evaluador.py")
        original = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(original)
        self.assertTrue(original.Evaluador().evaluar(self.parser.analizar("P(s(a))"))[0])


if __name__ == "__main__":
    unittest.main()
