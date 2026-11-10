---
name: generar-diapositivas
description: Use when producing contenido/capitulos/capNN/05-diapositivas.md from 02-libro.md — 14-18 slides with slide/pagina/titulo/layout front-matter and presenter notes, each pointing at a book page that actually exists, verified with verificar_sync.py.
---

# Generar diapositivas

De `02-libro.md` a `05-diapositivas.md`. La presentación **acompaña** el
libro que el productor tiene abierto; no lo repite ni lo sustituye.

## Qué leer antes

1. `contenido/ESQUEMA.md` — sincronización libro ↔ presentación.
2. `contenido/capitulos/capNN/02-libro.md` — y anotar todas las marcas
   `<!-- pagina: N -->`.
3. `contenido/capitulos/capNN/04-docente.md`, si existe — el guion de clase
   da los tiempos para las notas del expositor.
4. `contenido/capitulos/cap01/05-diapositivas.md` — ejemplo de formato.

## Pasos

1. **Construir el libro primero y leer su paginación real.**
   ```bash
   python3 build/scripts/construir_libro.py --capitulo capNN
   python3 -c "import json;print(json.load(open('salidas/libro/capNN-paginas.json'))['secciones'])"
   ```
   `salidas/libro/capNN-paginas.json` es **la autoridad**: lleva la página
   **global** del libro de cada sección, medida sobre el PDF. Las marcas
   `<!-- pagina: N -->` de `02-libro.md` son orientación; si discrepan, gana
   el JSON. El capítulo **no** empieza en la página 1: hay portada,
   créditos e índice delante.
2. **Planificar 14–18 diapositivas** cubriendo todas las páginas. Una
   página puede tener varias diapositivas; una diapositiva apunta a **una
   sola** página.
3. **Una diapositiva por bloque separado por `---`**, con front-matter:
   ```
   ---
   slide: 3
   pagina: 5
   titulo: "Tipos de biofertilizantes"
   layout: titulo-contenido
   ---
   ```
   `layout`: `portada`, `vinetas`, `columnas`, `tabla`, `imagen`, `dato`,
   `cierre` (se aceptan alias: `titulo-contenido`, `dos-columnas`,
   `comparacion`, `imagen-texto`). En `columnas`, partir el cuerpo con una
   línea `+++` o con dos subtítulos `###`, o el constructor avisa y manda
   todo a la primera columna.
   Añadir también `seccion: <slug-de-la-seccion>` tomado del JSON de
   paginación: con eso `verificar_sync.py` valida la diapositiva contra una
   sección concreta y no solo contra el rango del capítulo.
4. **Contenido de cada diapositiva:** un título que sea una afirmación, no
   una etiqueta («Entre más temprano, mejor», no «Momento de aplicación»).
   **Máximo 40 palabras de cuerpo** — `construir_presentacion.py` avisa por
   encima de ese umbral. Nada de párrafos: el párrafo va en el libro. Las
   notas del expositor no cuentan para ese límite, así que el detalle va
   ahí.
5. **Notas del expositor** en bloque `:::notas` al final de cada
   diapositiva, con:
   - el tramo de minutos del guion de `04-docente.md`
   - qué hacer en la pizarra o con material físico
   - la pregunta de discusión que corresponde
   - **el recordatorio explícito de qué dato está pendiente**, para que el
     docente no improvise un número
6. **Diapositiva 1** = portada (capítulo, módulo, institución). **Última**
   = cierre con lo accionable.
7. Si el capítulo es muestra: `[MUESTRA]` en el título de la portada y el
   aviso de muestra en el comentario de cabecera del archivo.

## Reglas

- **No introducir ningún dato que no esté en `02-libro.md`.** La
  presentación no es el lugar para «completar» el libro.
- Donde el libro tiene `<!-- FALTA: confirmar con el docente -->`, la
  diapositiva lo arrastra igual y las notas dicen «no improvisar».
- No poner la respuesta de un ejercicio en una diapositiva proyectada antes
  de que el grupo lo resuelva.
- Las páginas del libro deben quedar **todas** cubiertas por al menos una
  diapositiva.

## Verificar antes de terminar

- [ ] 14–18 diapositivas, numeración `slide:` consecutiva desde 1.
- [ ] Todo `pagina:` coincide con la página de su sección en
      `salidas/libro/capNN-paginas.json`.
- [ ] Toda diapositiva con `seccion:`, salvo la portada.
- [ ] `construir_presentacion.py` sin avisos (ni de palabras ni de layout).
- [ ] Cada página del libro aparece en al menos una diapositiva.
- [ ] Toda diapositiva tiene `:::notas`.
- [ ] Los tiempos de las notas suman la duración de `meta.yaml`.
- [ ] Ninguna diapositiva con más de 6 líneas de contenido.
- [ ] `verificar_sync.py` pasa.

## Build

```bash
python3 build/scripts/construir_presentacion.py --capitulo capNN
python3 build/scripts/verificar_sync.py --capitulo capNN
```
