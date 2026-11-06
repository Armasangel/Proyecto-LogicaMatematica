import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    import tkinter as tk
    _raiz = tk.Tk()
    _raiz.destroy()
    HAY_PANTALLA = True
except Exception:
    HAY_PANTALLA = False


@unittest.skipUnless(HAY_PANTALLA, "No hay pantalla/tkinter (use xvfb-run en Linux).")
class TestInterfaz(unittest.TestCase):
    def setUp(self):
        from controlador import Controlador
        from interfaz import VentanaPrincipal
        self.app = VentanaPrincipal(Controlador())
        self.addCleanup(self.app.destroy)

    def valor(self):
        return self.app.panel_resultado.etiqueta_valor.cget("text")

    def texto(self):
        return self.app.panel_resultado.texto.get("1.0", "end")

    def test_universal_falso_da_contraejemplo(self):
        self.app.evaluar()                      # ∀x ∃y M(x, y)
        self.assertEqual(self.valor(), "Falso")
        self.assertIn("contraejemplo x = 4", self.texto())

    def test_existencial_verdadero_da_testigo(self):
        self.app.p_formula.cargar("∃x P(x)")
        self.app.evaluar()
        self.assertEqual(self.valor(), "Verdadero")
        self.assertIn("testigo", self.texto())

    def test_pide_entorno_y_no_da_valor_sin_el(self):
        self.app.p_formula.cargar("P(x)")
        self.app.evaluar()
        self.assertEqual(self.valor(), "Error")
        self.assertIn("x", self.app.p_formula._combos)
        self.app.p_formula._combos["x"].set("2")
        self.app.evaluar()
        self.assertEqual(self.valor(), "Verdadero")
        self.app.p_formula._combos["x"].set("9")     # fuera de 𝒟
        self.app.evaluar()
        self.assertEqual(self.valor(), "Error")

    def test_errores_llevan_a_la_pestana_correcta(self):
        self.app.p_formula.cargar("P(a")
        self.app.evaluar()
        self.assertEqual(self.app.cuaderno.index("current"), 2)
        self.app.p_lenguaje.cargar("a, b", "s/1, suma/2", "P/1, M")
        self.app.evaluar()
        self.assertEqual(self.valor(), "Error")
        self.assertEqual(self.app.cuaderno.index("current"), 0)

    def test_funcion_incompleta_es_error_de_interpretacion(self):
        self.app.p_interp._funciones["s"].delete("1.0", "end")
        self.app.p_interp._funciones["s"].insert("1.0", "1 -> 2")
        self.app.evaluar()
        self.assertEqual(self.valor(), "Error")
        self.assertEqual(self.app.cuaderno.index("current"), 1)

    def test_rellenar_plantillas(self):
        self.app.p_interp._funciones["s"].delete("1.0", "end")
        self.app.p_interp.generar_plantillas()
        self.assertEqual(self.app.p_interp._funciones["s"].get("1.0", "end").count("->"), 4)


if __name__ == "__main__":
    unittest.main()
