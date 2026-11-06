import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import entrada_datos as d
from errores import ErrorLenguaje, ErrorSemantico
from evaluador import Evaluador


def interp_ejemplo():
    e = d.ejemplo()
    leng = d.construir_lenguaje(*e["lenguaje"])
    return leng, d.construir_interpretacion(
        leng, e["dominio"], e["constantes"], e["funciones"], e["relaciones"])


class TestEntradaDatos(unittest.TestCase):
    def test_ejemplo_equivale_al_evaluador_original(self):
        _, interp = interp_ejemplo()
        self.assertEqual(interp.dominio, (1, 2, 3, 4))
        self.assertEqual(interp.aplicar_funcion("suma", (3, 3)), 4)
        self.assertTrue(interp.satisface("M", (1, 2)))
        self.assertFalse(interp.satisface("M", (2, 2)))

    def test_lenguaje_formato(self):
        l = d.construir_lenguaje("a, b", "s/1; suma:2", "P/1")
        self.assertEqual(dict(l.funciones), {"s": 1, "suma": 2})
        with self.assertRaises(ErrorLenguaje):
            d.construir_lenguaje("a", "s", "P/1")          # falta aridad
        with self.assertRaises(ErrorLenguaje):
            d.construir_lenguaje("a", "s/1, s/2", "")       # repetido
        with self.assertRaises(ErrorLenguaje):
            d.construir_lenguaje("a", "a/1", "")            # categoría doble

    def test_errores_de_interpretacion(self):
        l = d.construir_lenguaje("c", "s/1", "P/1")
        base = dict(constantes_txt={"c": "1"}, funciones_txt={"s": "1->1\n2->2"},
                    relaciones_txt={"P": "1"})
        ok = d.construir_interpretacion(l, "1, 2", **base)
        self.assertEqual(ok.dominio, (1, 2))
        casos = [
            ("", base),                                                    # dominio vacío
            ("1, 1", base),                                                # duplicado
            ("1, 2", {**base, "constantes_txt": {}}),                      # constante sin valor
            ("1, 2", {**base, "constantes_txt": {"c": "9"}}),              # fuera de 𝒟
            ("1, 2", {**base, "funciones_txt": {"s": "1->1"}}),            # no total
            ("1, 2", {**base, "funciones_txt": {"s": "1->1\n2->"}}),       # sin salida
            ("1, 2", {**base, "funciones_txt": {"s": "1->1\n1->2"}}),      # entrada repetida
            ("1, 2", {**base, "funciones_txt": {"s": "1,2->1\n2->2"}}),    # aridad
            ("1, 2", {**base, "relaciones_txt": {"P": ""}}),               # relación vacía
            ("1, 2", {**base, "relaciones_txt": {"P": "(1,2)"}}),          # tupla de más
            ("1, 2", {**base, "relaciones_txt": {"P": "7"}}),              # fuera de 𝒟
        ]
        for dominio, kw in casos:
            with self.subTest(dominio=dominio, kw=kw):
                with self.assertRaises(ErrorSemantico):
                    d.construir_interpretacion(l, dominio, **kw)

    def test_plantilla(self):
        self.assertEqual(d.plantilla_funcion([1, 2], 2).count("->"), 4)
        with self.assertRaises(ErrorSemantico):
            d.plantilla_funcion(list(range(100)), 3)

    def test_entorno(self):
        self.assertEqual(dict(d.construir_entorno({"x": "2", "y": " "})), {"x": 2})

    def test_integracion_con_evaluador(self):
        leng, interp = interp_ejemplo()
        from analizador_sintactico import AnalizadorSintactico
        arbol = AnalizadorSintactico(leng).analizar("∃x (P(x) ∧ M(a, x))")
        valor, texto = Evaluador(interp).evaluar(arbol)
        self.assertTrue(valor)
        self.assertIn("testigo x = 2", texto)


if __name__ == "__main__":
    unittest.main()
