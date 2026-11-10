---
name: redactar-capitulo
description: Use when turning contenido/capitulos/capNN/01-fuente.md into a didactic 02-libro.md for farmers, using the ESQUEMA directive blocks and never inventing technical data (doses, strains, figures) that is not in the source.
---

# Redactar capítulo del libro

De `01-fuente.md` a `02-libro.md`: versión didáctica para **productores
agrícolas**, no para estudiantes de agronomía.

## Qué leer antes

1. `contenido/ESQUEMA.md` — bloques y reglas duras.
2. `contenido/capitulos/capNN/01-fuente.md` — **la única fuente de verdad**.
3. `contenido/capitulos/capNN/meta.yaml` — objetivos, duración, docente.
4. `contenido/capitulos/cap01/02-libro.md` — ejemplo de formato.

**Si `01-fuente.md` está vacío, parar y avisar.** No se redacta un capítulo
sin fuente; como mucho se produce una muestra y entonces se aplican las
reglas de muestra (ver abajo).

## Pasos

1. **Leer la fuente completa** antes de escribir una línea. Listar los temas
   que el docente cubrió y en qué orden.
2. **Planificar la paginación.** Unas 450–550 palabras equivalentes por
   página. Marcar el inicio de cada página con:
   ```
   <!-- pagina: N -->
   ```
   Un tema por página o por par de páginas; no partir un concepto en dos.
3. **Front-matter** con `capitulo`, `titulo`, `pagina_inicio`,
   `paginas_total`, `estado`.
4. **Página 1:** título, entrada corta que diga por qué le importa al
   productor, y `:::objetivos` (los de `meta.yaml`).
5. **Redactar cada página** con los bloques del esquema:
   - `:::objetivos` — solo en la página 1
   - `:::nota` — dato de apoyo, matiz
   - `:::ejemplo` — caso de campo concreto, con nombres de cultivos y zonas
   - `:::precaucion` — dosis, incompatibilidad, fitotoxicidad, pérdida de
     dinero
   - `:::glosario` — definir el término **la primera vez** que aparece
   - `:::sabias-que` — curiosidad que fija el concepto
   - `:::actividad` — ejercicio intercalado, hacible en 10–15 min
   - `:::figura{src="..." pie="..."}`
   - `:::tabla{titulo="..."}`
   Cerrar todos con `:::` en línea propia.
6. **Registro de escritura:** frases cortas, voz activa, segunda persona o
   impersonal. Nombrar **cultivos**, no familias botánicas («repollo y
   brócoli», no «crucíferas»). Toda palabra técnica se define en
   `:::glosario` la primera vez.
7. **Cerrar con `## Resumen del capítulo`**: 8–10 puntos numerados, cada
   uno accionable.
8. **Actualizar `meta.yaml`:** `paginas_total`, `estado`.

## Regla de no inventar datos (no negociable)

Un productor puede actuar sobre una dosis inventada y perder una cosecha.

- **Toda** dosis, concentración, UFC, precio, cepa comercial, umbral o
  porcentaje tiene que estar en `01-fuente.md`.
- Si no está, escribir en su lugar:
  ```
  <!-- FALTA: confirmar con el docente -->
  ```
  o un rango **etiquetado literalmente** «orientativo, verificar».
- Nunca rellenar con un número plausible de memoria.
- Nunca atribuir una afirmación a un docente que no la hizo.
- Para fechas de vencimiento, almacenamiento y dosis, la fórmula segura es
  «la etiqueta manda».

## Si es contenido de muestra

- `[MUESTRA]` en el título del capítulo y en el front-matter.
- Aviso al inicio del archivo, literal:
  «Contenido de muestra generado para demostrar el formato. Reemplazar con
  el material del docente antes de usar en clase.»
- `estado: muestra` y `es_muestra: true` en `meta.yaml`.
- `docente: null`. **Sin atribución a nadie.**

## Verificar antes de terminar

- [ ] Toda afirmación técnica rastreable a `01-fuente.md` (o marcada
      `FALTA`, o etiquetada como muestra).
- [ ] `grep -n "FALTA" 02-libro.md` — ningún número inventado donde debería
      haber un marcador.
- [ ] Bloques `:::` balanceados (cada apertura con su cierre).
- [ ] Marcas `<!-- pagina: N -->` consecutivas desde 1, sin saltos.
- [ ] `paginas_total` de `meta.yaml` == última marca de página.
- [ ] Todos los objetivos de `meta.yaml` cubiertos por el texto.
- [ ] Cada término técnico definido en `:::glosario` en su primera aparición.
- [ ] `wc -w 02-libro.md` coherente con las páginas declaradas.

## Build

```bash
python3 build/scripts/construir_libro.py --capitulo capNN
python3 build/scripts/verificar_sync.py --capitulo capNN
```
