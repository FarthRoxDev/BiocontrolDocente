---
name: edicion-docente
description: Use when producing contenido/capitulos/capNN/04-docente.md from 02-libro.md, 03-ejercicios.md and 05-diapositivas.md — timed lesson script, reasoned answer per exercise, common farmer mistakes, and discussion questions.
---

# Edición docente

De los otros archivos del capítulo a `04-docente.md`. Es lo último que se
escribe: necesita el libro, los ejercicios y las diapositivas ya hechos.

## Qué leer antes

1. `contenido/ESQUEMA.md`
2. `contenido/capitulos/capNN/02-libro.md` — con sus marcas de página
3. `contenido/capitulos/capNN/03-ejercicios.md` — enunciados **y** clave
4. `contenido/capitulos/capNN/05-diapositivas.md` — numeración y páginas
5. `contenido/capitulos/capNN/meta.yaml` — duración, materiales
6. `plantillas/docente/README.md` — qué secciones consume la maquetación
7. `contenido/capitulos/cap01/04-docente.md` — ejemplo de formato

## Estructura obligatoria

1. **Antes de la clase** — tabla de cabecera (duración, páginas,
   diapositivas, nº de ejercicios), revisión con 48 h de antelación,
   materiales de `meta.yaml`, y el **riesgo pedagógico** del capítulo.
2. **Guion de clase** — tramos con minutos (`15–30 min · Micorrizas`), y en
   cada tramo: la diapositiva y la página del libro, la idea única que debe
   quedar, qué hacer en pizarra o con material físico, y la pregunta de
   discusión.
3. **Errores comunes del productor** — tabla: error · cómo se ve en campo ·
   cómo corregirlo en clase. Mínimo 8 filas.
4. **Preguntas para generar discusión** — 6–10, abiertas, sin respuesta
   única.
5. **Respuestas explicadas, ejercicio por ejercicio** — **todos** los
   ejercicios de `03-ejercicios.md`, en orden, con: la respuesta, **por qué**
   es la correcta, qué error representa cada distractor, y dónde se tranca
   el grupo.
6. **Si el tiempo se acorta** — orden de recorte, y qué no se recorta nunca.
7. **Para la próxima versión** — lista de casillas con lo pendiente,
   empezando por los marcadores `FALTA`.

## Reglas

- Los tiempos del guion tienen que **sumar** la `duracion_min` de
  `meta.yaml`, y coincidir con los tramos citados en las notas de
  `05-diapositivas.md`.
- Las referencias a diapositivas y páginas deben existir. Verificarlas, no
  suponerlas.
- **No introducir datos técnicos nuevos.** Si un error común requiere una
  cifra que el libro no da, se describe cualitativamente o se marca
  `<!-- FALTA: confirmar con el docente -->`.
- Instrucciones al docente, no ensayo: imperativo y concreto («cortar los
  nódulos frente al grupo»), no «se recomienda considerar».
- Si el capítulo es muestra: `[MUESTRA]` en el título, aviso de muestra al
  inicio y **ninguna atribución a ningún profesor**.

## Verificar antes de terminar

- [ ] Las siete secciones presentes.
- [ ] Los tramos del guion suman `duracion_min`.
- [ ] Cada tramo cita una diapositiva y una página que existen (las páginas,
      contra `salidas/libro/capNN-paginas.json`).
- [ ] **Todos** los ejercicios tienen respuesta explicada, subítems
      incluidos.
- [ ] Las respuestas coinciden con la clave de `03-ejercicios.md` (comparar
      una por una; si discrepan, corregir el archivo que esté mal, no
      ocultar la diferencia).
- [ ] ≥ 8 errores comunes y ≥ 6 preguntas de discusión.
- [ ] Ningún dato técnico ausente del libro.

## Build

```bash
python3 build/scripts/construir_libro.py --capitulo capNN
python3 build/scripts/verificar_sync.py --capitulo capNN
```
La edición docente propiamente dicha (franja lateral, cuadro «antes de la
clase», minutaje al margen) **todavía no la emite el build**: su
especificación está en `plantillas/docente/README.md` y la implementa el
agente de maquetación. Comprobar con `--help` si ya existe una bandera de
edición antes de prometerla.
