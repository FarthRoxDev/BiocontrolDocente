---
name: generar-ejercicios
description: Use when producing contenido/capitulos/capNN/03-ejercicios.md from 02-libro.md — 12-15 varied exercises (multiple choice, true/false, matching columns, field case, simple calculation) with a page reference each and an answer key at the end.
---

# Generar ejercicios

De `02-libro.md` a `03-ejercicios.md`. **Solo se evalúa lo que el libro
enseñó.**

## Qué leer antes

1. `contenido/ESQUEMA.md`
2. `contenido/capitulos/capNN/02-libro.md` — completo, con sus marcas de
   página
3. `contenido/capitulos/capNN/meta.yaml` — objetivos de aprendizaje
4. `contenido/capitulos/cap01/03-ejercicios.md` — ejemplo de formato

## Pasos

1. **Mapear objetivos → páginas.** Cada objetivo de `meta.yaml` tiene que
   quedar cubierto por al menos un ejercicio.
2. **Repartir 12–15 ejercicios** por tipo, agrupados en secciones:
   | Sección | Tipo | Cuántos |
   |---|---|---|
   | A | Selección única (4 opciones, 1 correcta) | 4–5 |
   | B | Falso / verdadero (en tabla, 5 ítems cada uno) | 2 |
   | C | Relacionar columnas | 2–3 |
   | D | Caso de campo (situación realista, varias preguntas) | 2–3 |
   | E | Cálculo sencillo (regla de tres, áreas, dosis por tanque) | 1–2 |
3. **Cada ejercicio** lleva número, título corto y la página del libro que
   evalúa, en cursiva: `*(página 7)*`.
4. **Distractores útiles** en la selección única: cada opción incorrecta
   debe corresponder a un error real que comete el productor, no a un
   relleno absurdo. Así el ejercicio sirve de diagnóstico.
5. **Casos de campo:** nombres propios, cultivos y zonas verosímiles del
   país; que el productor se reconozca. Preguntar «identifique cuatro
   errores y qué debió hacer», no «comente».
6. **Cálculos:** aritmética de finca (litros por hectárea, tanques de bomba,
   gramos por bolsa, conversión ha ↔ m²). Si las dosis reales no están
   confirmadas, usar números **ficticios y declararlo en voz alta** en el
   enunciado, con `<!-- FALTA: confirmar con el docente -->` al lado.
7. **Clave de respuestas al final**, tras un separador, con el título
   `# Clave de respuestas`. Para cada ejercicio: la respuesta, y en los
   falso/verdadero el motivo del falso en una línea. El razonamiento
   extenso va en `04-docente.md`, no aquí.
8. Front-matter con `capitulo`, `titulo`, `estado`, `ejercicios_total`.

## Reglas

- **No introducir datos nuevos.** Si un ejercicio necesita una dosis que el
  libro no da, se cambia el ejercicio, no se inventa la dosis.
- No evaluar nada que esté marcado `FALTA` en el libro.
- Un ejercicio, un concepto. Nada de preguntas con dos trampas a la vez.
- Lenguaje de productor, no de examen universitario.
- Si el capítulo es muestra: `[MUESTRA]` en el título y el aviso de muestra
  al inicio.

## Verificar antes de terminar

- [ ] 12–15 ejercicios, todos los tipos presentes.
- [ ] Cada ejercicio cita una página que existe en `02-libro.md`.
- [ ] Cada objetivo de `meta.yaml` evaluado al menos una vez.
- [ ] La clave cubre **todos** los ejercicios y todos los subítems.
- [ ] Las respuestas de la clave coinciden con lo que dice el libro
      (releer la página citada, una por una).
- [ ] Los cálculos resueltos a mano: las cuentas dan.
- [ ] Ningún dato técnico que no esté en `02-libro.md`.

## Build

```bash
python3 build/scripts/construir_libro.py --capitulo capNN
```
