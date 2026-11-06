# Evaluador semántico – Lógica de primer orden (MM3032)

Aplicación gráfica que decide si una fórmula es verdadera o falsa en una
interpretación finita ingresada por el usuario, y explica por qué.

## Ejecutar

```bash
python src/main.py                            # interfaz (Python ≥ 3.10, solo biblioteca estándar)
python -B -m unittest discover -s tests -v    # pruebas
xvfb-run -a python -B -m unittest discover -s tests -v   # Linux sin pantalla (incluye la GUI)
```

## Uso (3 pestañas)

1. **Lenguaje:** constantes (`a, b`), símbolos funcionales (`s/1, suma/2`) y predicados (`P/1, M/2`).
2. **Interpretación:** dominio `1, 2, 3, 4`; valor de cada constante; tabla de cada función
   (una línea por entrada, `1, 2 -> 3`) y relación de cada predicado (una tupla por línea, `(1, 2)`).
   El botón *Rellenar tablas de funciones vacías* genera todas las entradas de 𝒟ⁿ.
3. **Fórmula y entorno:** botones ¬ ∧ ∨ → ∀ ∃ ( ) o teclado (`~ ! & | -> forall exists`).
   Las variables libres se detectan y piden un valor de 𝒟 (entorno σ).

El resultado muestra **Verdadero/Falso** y la justificación: testigo (∃ verdadero),
contraejemplo (∀ falso) o comprobación completa (∀ verdadero / ∃ falso). Cualquier error de
sintaxis, símbolos, aridades, dominio, tuplas o asignaciones **no recibe valor de verdad** y
lleva a la pestaña donde está el problema. Botón *Cargar ejemplo* para una demostración rápida.

Detalles de la sintaxis y validación: ver `PERSONA2.md`.

## Estructura

| Archivo | Rol |
| --- | --- |
| `src/interfaz.py`, `paneles_entrada.py`, `panel_resultado.py`, `teclado_logico.py` | Interfaz |
| `src/entrada_datos.py` | Texto de la interfaz → `Lenguaje`, `Interpretacion`, `Entorno` |
| `src/controlador.py` | Conecta interfaz, parser y evaluador |
| `src/analizador_sintactico.py`, `tokenizer.py`, `nodos.py`, `lenguaje.py`, `validacion.py` | Sintaxis y validación |
| `src/interpretacion.py` | Dominio, f^ℐ, P^ℐ y entornos σ |
| `evaluador.py` (raíz) + `src/evaluador.py` | Evaluación semántica y justificaciones |
