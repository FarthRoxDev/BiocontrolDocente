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

1. **Listar las páginas reales del libro.**
   `grep -n "pagina: " 02-libro.md`
   Ninguna diapositiva puede apuntar a una página que no esté en esa lista.
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
   `layout`: `portada`, `titulo-contenido`, `dos-columnas`, `comparacion`,
   `tabla`, `imagen-texto`, `cierre`.
4. **Contenido de cada diapositiva:** un título que sea una afirmación, no
   una etiqueta («Entre más temprano, mejor», no «Momento de aplicación»).
   Como máximo 6 líneas o 5 viñetas. Nada de párrafos: el párrafo va en el
   libro.
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
- [ ] Todo `pagina:` existe como `<!-- pagina: N -->` en `02-libro.md`
      (comparar las dos listas con `grep`).
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
