# Persona 2: sintaxis y validación

Implementación de los requerimientos 1, 3 y 7, con identificación de variables libres y ligadas para que la interfaz solicite el entorno. Requiere Python 3.10 o posterior y utiliza únicamente la biblioteca estándar.

El paquete contiene solamente archivos nuevos para agregar a la raíz del repositorio conservando las carpetas `src` y `tests`. Necesita el `evaluador.py` original en la raíz. No reemplazar archivos existentes si se instala sobre otra versión del proyecto.

## Ejecutar

Desde la raíz del repositorio:

```powershell
python src/main.py
python ejemplo_persona2.py
python -B -m unittest discover -s tests -v
```

La aplicación existente funciona con su interpretación de ejemplo: dominio `{1,2,3,4}`, constantes `a=1`, `b=3`, funciones `s/1`, `suma/2`, predicados `P/1` (pares) y `M/2` (menor que). Por ejemplo: `P(s(a))`, `∃x P(x)` y `∀x (P(x) ∨ ¬P(x))`.

No se cambió ningún archivo anterior. El nuevo `src/evaluador.py` carga el `evaluador.py` original de la raíz y hereda su implementación; valida antes de delegar la evaluación. Por eso el import ya presente en `src/controlador.py` conecta los módulos nuevos sin editar el controlador. No se duplicó la lógica de evaluación ni de justificaciones.

Para conservar esta validación, importar `Evaluador` desde `src` como hace el controlador. Ejecutar directamente el archivo original de la raíz no instala el adaptador.

## Archivos y responsabilidades

| Archivo nuevo | Responsabilidad |
| --- | --- |
| `src/lenguaje.py` | Declaraciones, nombres, categorías y aridades |
| `src/tokenizer.py` | Tokens con posición original |
| `src/analizador_sintactico.py` | Parser descendente y construcción del AST |
| `src/nodos.py` | Términos, fórmulas, variables libres y ligadas |
| `src/interpretacion.py` | Dominio, constantes, funciones, relaciones y entorno |
| `src/validacion.py` | Validación completa del AST y sus entradas |
| `src/errores.py` | Errores para la interfaz, con posición o campo |
| `src/evaluador.py` | Validación previa al evaluador existente |
| `tests/test_persona2.py` | Pruebas de sintaxis, datos e integración |
| `ejemplo_persona2.py` | Demostración con un lenguaje personalizado |

## Gramática y precedencia

```text
formula      := implicacion
implicacion  := disyuncion [ '→' implicacion ]
disyuncion   := conjuncion { '∨' conjuncion }
conjuncion   := prefijo { '∧' prefijo }
prefijo      := '¬' prefijo
              | ('∀' | '∃') variable [ '.' ] prefijo
              | '(' formula ')'
              | predicado '(' [ termino { ',' termino } ] ')'
termino      := variable | constante
              | funcion '(' [ termino { ',' termino } ] ')'
```

Los predicados y funciones de aridad cero admiten tanto `Q()` / `g()` como `Q` / `g` en su categoría correspondiente.

Orden de mayor a menor precedencia: paréntesis; prefijos `¬`, `∀`, `∃`; `∧`; `∨`; `→`. Conjunción y disyunción se agrupan a la izquierda. Implicación se agrupa a la derecha: `P(a) → P(b) → P(a)` significa `P(a) → (P(b) → P(a))`.

El cuantificador alcanza el prefijo que sigue. `∀x P(x) → P(x)` deja libre la segunda `x`; escribir `∀x (P(x) → P(x))` para cuantificar toda la implicación. Para separar una variable de un predicado sin paréntesis, usar espacio: `∀x P(x)`. También se admite `∀x(P(x))`.

Se admiten alias de teclado: `~` / `!`, `&`, `|`, `->`, `forall`, `exists`. Los nombres tienen la forma `[A-Za-z_][A-Za-z_0-9]*`, distinguen mayúsculas y minúsculas, y no pueden ser `forall` ni `exists`.

Un identificador no declarado que aparece como término sin argumentos se interpreta como variable, ya que las variables no se declaran. Un predicado desconocido o una función desconocida con paréntesis siempre es un error. Los nombres de símbolos declarados no se pueden reutilizar como variables.

## API para configurar e integrar con la interfaz

Los siguientes imports se utilizan desde `src` o agregando `src` al `sys.path`, como en `ejemplo_persona2.py`:

```python
from analizador_sintactico import AnalizadorSintactico
from evaluador import Evaluador
from interpretacion import Interpretacion, Entorno
from lenguaje import Lenguaje
from nodos import variables_libres, variables_ligadas

lenguaje = Lenguaje(
    constantes=["c"],
    funciones={"s": 1},
    predicados={"P": 1},
)
interpretacion = Interpretacion(
    dominio=[1, 2],
    constantes={"c": 1},
    funciones={"s": (1, {(1,): 2, (2,): 2})},
    relaciones={"P": (1, {(2,)})},
    lenguaje=lenguaje,
)
parser = AnalizadorSintactico(lenguaje)
arbol = parser.analizar("P(x) ∧ P(s(c))")
libres = variables_libres(arbol)      # {"x"}: pedir su valor en la interfaz
ligadas = variables_ligadas(arbol)    # set()
entorno = Entorno({"x": 2})
valor, explicacion = Evaluador(interpretacion, entorno).evaluar(arbol)
```

`parser.analizar_con_variables(texto)` devuelve `(arbol, libres, ligadas)`. Un nombre puede aparecer en ambos conjuntos cuando tiene ocurrencias libres y ligadas en distintas partes de la fórmula. `variables_ligadas` incluye los nombres introducidos por cuantificadores, incluso cuantificadores vacuos.

La interfaz actual recibe solamente el texto de la fórmula. No se agregaron ni cambiaron pantallas. La captura gráfica del lenguaje, interpretación y entorno corresponde a la integración de interfaz del equipo. Para conectarla, se pueden asignar los módulos al controlador existente:

```python
controlador.analizador = AnalizadorSintactico(lenguaje)
controlador.evaluador = Evaluador(interpretacion, entorno)
resultado = controlador.evaluar("P(x)")
```

Antes de llamar a `evaluar`, analizar la fórmula y solicitar un valor del dominio para cada variable libre. Si falta un valor, se devuelve un error sin valor de verdad.

## Reglas de validación

- El dominio debe ser no vacío y no tener duplicados. Sus elementos deben ser hashables, como números, cadenas o tuplas hashables. Usar una lista al capturar datos para poder detectar repeticiones antes de convertirlas en un conjunto.
- Cada símbolo debe tener una única categoría y una aridad entera no negativa. Una constante representa un símbolo funcional de aridad cero; también se pueden declarar funciones con aridad cero mediante `funciones`.
- Cuando se suministra `lenguaje`, la interpretación debe coincidir exactamente con sus declaraciones y aridades. Si no se suministra, se infiere de las constantes, funciones y relaciones recibidas, para mantener la compatibilidad con el evaluador original.
- Cada constante debe pertenecer al dominio.
- Cada función se recibe como `(aridad, tabla)` con claves tupla y valores en el dominio. Debe definir todas las entradas de `D^n`. Se rechazan tablas vacías, tuplas inválidas, entradas normalizadas duplicadas y valores fuera del dominio.
- Por compatibilidad con el evaluador existente se aceptan callables de Python para funciones. Se ejecutan para todas las entradas de `D^n`, se comprueban sus resultados y se conserva una tabla. El texto de usuario nunca se ejecuta ni se pasa a `eval`.
- Cada relación se recibe como `(aridad, colección_de_tuplas)`. Debe ser no vacía, con longitud correcta y elementos del dominio. Para relaciones unarias se admiten tanto `{(1,), (2,)}` como `{1, 2}`. La prohibición de relaciones vacías sigue el enunciado del proyecto.
- Para aridad cero, `D^0` contiene la tupla vacía `()`: una función tiene tabla `{(): valor}` y una relación no vacía tiene `{()}`.
- Se requiere una asignación del dominio por variable libre. También se rechazan asignaciones adicionales con valores inválidos. Las asignaciones de símbolos declarados se rechazan porque no son variables.
- Se valida el AST completo antes de evaluar. Por ejemplo, un antecedente falso no permite omitir una variable libre sin asignación en el consecuente. Un error produce `Resultado.valor is None` a través del controlador existente.

Las colecciones de entrada se copian; las tablas y relaciones normalizadas no se modifican por cambios posteriores en los diccionarios originales. Crear una nueva `Interpretacion` para cambiar los datos.

La comprobación de totalidad visita `|D|^n` entradas por función; es el costo esperado de validar explícitamente una interpretación finita.

## Errores

Los errores heredan de `ErrorValidacion` (`ValueError`). Los de fórmula incluyen `posicion` (índice desde cero), `linea` y `columna` (desde uno), además del texto y un indicador `^`. Los mensajes al usuario muestran la posición desde uno. Los errores de datos incluyen `ruta`, como `funciones.s` o `relaciones.P[0][1]`, porque esos datos no tienen una posición en la fórmula.

```text
's' espera 1 argumento(s), recibió 2. (línea 1, columna 3, posición 3)
P(s(c, c))
  ^
```

## Verificación

Las pruebas cubren precedencia, asociatividad, paréntesis, cuantificadores, sombreado, aridades cero, símbolos desconocidos, posiciones, totalidad de funciones, tuplas, dominio, entorno, errores en ramas omitidas por cortocircuito y compatibilidad con el controlador y las justificaciones originales. Se verificó la integración sin abrir una ventana gráfica.
