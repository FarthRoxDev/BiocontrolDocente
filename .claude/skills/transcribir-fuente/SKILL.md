---
name: transcribir-fuente
description: Use when converting a teacher's original material (PPTX, DOCX, PDF, scans, audio) into contenido/capitulos/capNN/01-fuente.md as a faithful transcription — no interpreting, no completing, marking anything unreadable. Use before redactar-capitulo.
---

# Transcribir fuente del docente

Convierte el material original del profesor en `01-fuente.md`. **Fiel, no
didáctico.** La redacción viene después.

## Qué leer antes

1. `contenido/ESQUEMA.md` — contrato de formato.
2. `contenido/capitulos/capNN/meta.yaml` — a qué capítulo pertenece.
3. `contenido/capitulos/cap01/01-fuente.md` — plantilla de referencia.

## Pasos

0. **Probar primero el ingestor automático.** Para PPTX, DOCX y PDF con texto
   resuelve el 90 % del trabajo, incluidas las imágenes:

   ```bash
   python3 build/scripts/ingerir_fuentes.py contenido/fuentes/<archivos> \
       --capitulo capNN --docente "Nombre del docente"
   ```

   Escribe `01-fuente.md` y guarda las imágenes incrustadas en
   `diseno/assets/capNN/`, dejando en el markdown la ruta relativa lista para
   pegar en un bloque `:::figura`. Revisá su salida y completá a mano solo lo
   que haya marcado: gráficos nativos de PowerPoint (no se pueden extraer),
   páginas escaneadas sin texto, y formatos EMF/WMF que hay que reexportar a
   PNG. Los pasos de abajo son para lo que el ingestor no cubre: escaneos,
   fotos de pizarra y audio.

1. **Guardar el original intacto** en `referencias/`. No editarlo nunca.
2. **Extraer el texto** según el formato:
   - PPTX: `python3 -c` con `python-pptx`, o descomprimir y leer
     `ppt/slides/slideN.xml`. Extraer **también las notas del expositor**.
   - DOCX: `python-docx`, o descomprimir y leer `word/document.xml`.
   - PDF: `pdftotext -layout`. Si sale vacío, es un PDF escaneado: leer las
     páginas como imagen con la herramienta de lectura y transcribir a mano.
   - Imágenes y fotos de pizarra: leerlas y transcribir.
   - Audio: si no hay transcripción disponible, **no inventarla**: pedirla.
3. **Volcar en orden**, una sección `## Diapositiva N` / `## Página N` por
   cada unidad del original. Mismo orden que el docente, aunque parezca
   desordenado.
4. **Transcribir literal.** No corregir la gramática, no reordenar, no
   completar frases, no unificar terminología, no «mejorar». Si el docente
   dijo algo discutible o incompleto, se transcribe así.
5. **Marcar lo que no se puede leer:**
   - `[ILEGIBLE]` — texto que no se distingue
   - `[INAUDIBLE]` — audio que no se entiende
   - `[DUDOSO: texto propuesto]` — se cree leer eso, sin certeza
   - `[FIGURA: descripción de lo que se ve]`
   - `[TABLA: n filas x m columnas]` y transcribirla abajo
6. **Figuras:** describir **lo que se ve**, no lo que se supone que
   significa. Llenar la tabla «Figuras del original».
7. **Datos numéricos:** llenar la tabla «Datos numéricos mencionados por el
   docente» con el valor **textual** y su unidad tal como aparece. Si no
   quedó claro, dejar `<!-- FALTA: confirmar con el docente -->` y
   **no estimar**.
8. **Dudas:** acumular en el apartado final preguntas concretas para el
   docente.
9. **Actualizar `meta.yaml`:** `docente`, `fuente_material`,
   `fecha_material`, `estado: borrador`.

## Prohibido

- Inventar o parafrasear contenido que no está en el original.
- Rellenar un hueco con conocimiento general de agronomía.
- Atribuir al docente algo que no dijo.
- Borrar los marcadores de incertidumbre «para que quede limpio».

## Verificar antes de terminar

- [ ] Cada diapositiva/página/bloque del original tiene su sección, en orden.
- [ ] Nº de secciones == nº de unidades del original (contarlas).
- [ ] Todo lo ilegible está marcado; no hay huecos silenciosos.
- [ ] Tablas «Figuras», «Tablas» y «Datos numéricos» llenas o explícitamente
      vacías.
- [ ] `meta.yaml` tiene `docente` y `fuente_material`.
- [ ] El original está en `referencias/` sin modificar.

## Build

```bash
python3 build/scripts/verificar_sync.py --capitulo capNN
```
