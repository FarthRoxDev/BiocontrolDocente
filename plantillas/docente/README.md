# Plantilla de la edición docente

Especificación de lo que la **edición docente** agrega respecto al **libro
del productor**. La escribe el agente de contenido; la implementa el agente
de maquetación en `plantillas/docente/`.

## Principio

**Misma retícula, mismo número de páginas, misma numeración.** La edición
docente es el libro del productor *más* una franja lateral y unos bloques
propios. Si el productor abre la página 7 y el docente abre la página 7,
tienen que estar viendo lo mismo en la mancha principal. Esto es lo que
hace posible decir «vayan a la página 7» en clase.

| | Libro del productor | Edición docente |
|---|---|---|
| Formato | A4 vertical | **A4 horizontal** (apaisado) |
| Mancha | Una columna, márgenes del libro | **Misma columna, misma posición** |
| Extra | — | Franja lateral derecha para el docente |
| Numeración | 1..N | **Idéntica** |
| Fuente | `02-libro.md` | `02-libro.md` + `03-ejercicios.md` + `04-docente.md` |
| Salida | `salidas/libro/` | `salidas/docente/` |

El apaisado existe solo para hacer sitio a la franja: la mancha del
productor conserva su ancho y su posición relativa, y la franja ocupa el
espacio ganado a la derecha.

## Secciones extra

### 1. Franja lateral de respuestas

Columna fija al borde exterior de cada página, de aproximadamente un tercio
del ancho útil, separada por un filete fino (`--bc-linea`) y con fondo
`--bc-papel-alt` para distinguirla de la mancha del productor.

Contiene, en este orden de prioridad cuando no cabe todo:

1. **Respuestas de los bloques `:::actividad`** de esa misma página, a la
   altura del bloque que responden.
2. **Respuestas de los ejercicios** de `03-ejercicios.md` cuyo campo
   `*(página N)*` apunte a esa página.
3. **Notas al margen** de `04-docente.md` ancladas a esa página.
4. **Marcadores `<!-- FALTA: confirmar con el docente -->`** de esa página,
   renderizados visiblemente (no como comentario oculto) con el color
   `--bc-alerta-600`. El docente tiene que ver lo que falta antes de
   dictar; en el libro del productor, en cambio, no se imprimen.

Reglas:

- La franja **no desplaza** la mancha del productor ni cambia sus saltos de
  línea o de página.
- Si el contenido de la franja no cabe, continúa en la franja de la página
  siguiente con la nota «sigue →». Nunca se corta en silencio.
- Tipografía `--bc-t-pie`, interlínea compacta.
- Si la franja queda vacía en una página, el espacio se deja en blanco. No
  se rellena ni se reflow.

### 2. Cuadro «Antes de la clase»

Una página propia **al inicio de cada capítulo**, antes de la página 1, sin
numeración (o numerada como `0`), construida a partir del apartado
«Antes de la clase» de `04-docente.md`. Lleva:

- Tabla de cabecera: duración, páginas del libro, diapositivas, nº de
  ejercicios.
- Lista de revisión con 48 horas de antelación.
- **Materiales de clase** (de `meta.yaml: materiales_clase`), como lista con
  casillas de verificación imprimibles.
- **Riesgo pedagógico** del capítulo.
- **Aviso de datos pendientes**: si `meta.yaml` tiene
  `datos_pendientes: true`, una banda de alerta a todo el ancho con el
  recuento de marcadores `FALTA` del capítulo.
- Si `meta.yaml` tiene `es_muestra: true`, la banda de muestra con el texto
  de `aviso_muestra`.

### 3. Tiempos sugeridos

Dos presentaciones del mismo dato, sacadas del guion de clase de
`04-docente.md`:

- **Barra de tiempo del capítulo** en la página «Antes de la clase»: una
  franja horizontal con los tramos del guion proporcionales a su duración,
  rotulada en minutos.
- **Marca de minutaje al margen superior de cada página**: el tramo del
  guion que corresponde a esa página, en formato `55–70 min`, en
  `--bc-t-micro` y color `--bc-tinta-suave`. Si una página no tiene tramo
  asignado, no se imprime nada.

### 4. Bloques exclusivos de la edición docente

Se escriben en `04-docente.md` y **solo** se renderizan en esta edición. El
libro del productor los ignora por completo.

| Bloque | Dónde se coloca | Color |
|---|---|---|
| `:::docente-guion` | franja lateral o pie de página | `--bc-verde-100` |
| `:::docente-error` (error común del productor) | franja lateral | `--bc-alerta-100` |
| `:::docente-discusion` (pregunta para el grupo) | franja lateral | `--bc-agua-100` |
| `:::docente-respuesta` (respuesta razonada) | franja lateral | `--bc-papel-alt` |
| `:::docente-recorte` (qué sacrificar si falta tiempo) | pie de la página inicial | `--bc-tierra-100` |

### 5. Referencia a la diapositiva

En la cabecera de cada página, junto al número de página, el rango de
diapositivas de `05-diapositivas.md` que apuntan a esa página
(`pagina:` == N). Formato: `◻ 4–5`. Permite al docente saber dónde está sin
mirar la pantalla.

### 6. Pliego de ejercicios con clave intercalada

Los ejercicios de `03-ejercicios.md` se imprimen al final del capítulo,
igual que en el libro del productor, pero:

- Cada ejercicio lleva su **respuesta razonada** de `04-docente.md`
  inmediatamente debajo, en recuadro `--bc-verde-100`.
- Se marca con un icono cuáles se resuelven en el aula y cuáles quedan de
  tarea, según el guion de clase.
- La clave suelta del final de `03-ejercicios.md` **no** se repite: ya está
  intercalada.

## Reglas duras para el agente de maquetación

1. **No alterar el flujo del libro del productor.** La edición docente se
   compone sobre la misma paginación. Si la franja fuerza un cambio de
   página en la mancha principal, es un error de implementación.
2. **Los marcadores `FALTA` se imprimen visibles** en la edición docente y
   **se omiten** en la del productor.
3. Si `es_muestra: true`, cada página lleva la banda de muestra. No se
   compone una edición docente de muestra sin ella.
4. No se inventa contenido para llenar la franja. Franja vacía es un
   resultado válido y además es la señal de que falta escribir
   `04-docente.md`.
5. Colores y tipografías **solo** desde `diseno/css/tokens.css`
   (`var(--bc-*)`). No definir colores nuevos aquí.

## Archivos que debe producir esta plantilla

```
plantillas/docente/
  README.md          ← este archivo (especificación)
  docente.css        ← estilos de la edición: franja, bandas, bloques
  pagina.html        ← plantilla de página con mancha + franja
  antes-de-clase.html← plantilla del cuadro de apertura del capítulo
```

## Build

La bandera de edición **aún no existe** en `construir_libro.py` (hoy acepta
`--capitulo`, `--salida`, `--fuente`, `--ejercicios`, `--sin-pdf`).
Implementarla como parte de esta plantilla:

```bash
python3 build/scripts/construir_libro.py --capitulo cap01 --edicion docente
python3 build/scripts/verificar_sync.py --capitulo cap01
```

Mientras no exista, la edición docente se compone a mano desde
`salidas/libro/cap01.html` y `salidas/libro/cap01-paginas.json`, que ya
traen la paginación global medida sobre el PDF.


---

## Estado

La bandera `--edicion docente` de `construir_libro.py` **ya esta implementada**:
agrega `diseno/css/docente.css` sobre `libro.css`, anexa `04-docente.md` como
seccion «Solo para el docente» y escribe en `salidas/docente/`. La edicion
docente reimprime el libro del productor identico y le suma la guia, para que
el docente estudie exactamente la pagina que el productor tiene delante.
