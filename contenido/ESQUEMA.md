# Esquema de contenido — contrato para agentes y skills

Cada capítulo vive en `contenido/capitulos/capNN/` con estos archivos:

| Archivo | Rol |
|---|---|
| `meta.yaml` | metadatos: título, autor docente, duración, objetivos |
| `01-fuente.md` | **transcripción fiel** del material del profesor (sin invención) |
| `02-libro.md` | versión didáctica redactada, con bloques marcados |
| `03-ejercicios.md` | ejercicios numerados + clave de respuestas |
| `04-docente.md` | notas ampliadas, errores comunes, guion de clase |
| `05-diapositivas.md` | una diapositiva por `---`, sincronizada por `pagina:` |

## Bloques didácticos (sintaxis en `02-libro.md`)

Se escriben como contenedores de directiva (`:::`). El renderizador los
convierte en cajas con el color del token correspondiente.

```
:::objetivos
- Identificar los tipos de biofertilizante.
:::

:::nota            (azul agua — dato de apoyo)
:::ejemplo         (ocre tierra — caso práctico de campo)
:::precaucion      (alerta — dosis, incompatibilidad, fitotoxicidad)
:::glosario        (verde claro — definición de término)
:::sabias-que      (verde claro — curiosidad)
:::actividad       (ejercicio intercalado en la página)
:::figura{src="../../../diseno/assets/capNN/foto.jpg" pie="..."}
:::tabla{titulo="..."}
```

## Sincronización libro ↔ presentación

Cada diapositiva declara en su front-matter la página del libro que acompaña:

```
---
slide: 3
pagina: 12          # página del libro que el productor tiene abierta
titulo: "Tipos de biofertilizantes"
---
```

El script `build/scripts/verificar-sync.py` falla si una diapositiva
apunta a una página que el libro no produjo.

## Figuras

`ingerir_fuentes.py` extrae las imágenes incrustadas del material del docente a
`diseno/assets/capNN/` y deja en `01-fuente.md` la referencia con la ruta
relativa ya correcta: se copia tal cual dentro de un bloque `:::figura`.

El ingestor marca por su cuenta lo que conviene mirar: imágenes repetidas
(logos de plantilla), imágenes muy pequeñas (probablemente decorativas) y
formatos que el PDF no puede incrustar (EMF/WMF, hay que reexportarlos a PNG).
Los gráficos nativos de PowerPoint **no se pueden extraer**: el ingestor los
señala para rehacerlos o pedirle una captura al docente.

## Reglas duras

1. **Nunca inventar datos técnicos** (dosis, cepas, cifras) que no estén en
   `01-fuente.md`. Si falta, marcar `<!-- FALTA: confirmar con el docente -->`.
2. Todo contenido de muestra se marca con `[MUESTRA]` en el título.
3. Atribución del capítulo al docente que aportó el material, en `meta.yaml`.
