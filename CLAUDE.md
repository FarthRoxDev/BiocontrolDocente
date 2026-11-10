# BiocontrolDocente

Proyecto de producción editorial para el curso de biocontrol del Lab Biocontrol CIB (TEC).
Convierte el material que entregan los docentes en tres entregables sincronizados por capítulo:

1. **Libro del productor** — libro de texto didáctico (A4, estilo escolar), con ejercicios y notas.
2. **Presentación** — mazo 16:9 que el expositor pasa mientras el productor sigue el libro.
3. **Edición docente** — el mismo libro con respuestas, guion de clase y notas ampliadas.

## Flujo de trabajo

```
material del docente (.pptx/.docx/.pdf)
  └─ build/scripts/ingerir_fuentes.py  ──>  01-fuente.md   (transcripción fiel)
       └─ skill redactar-capitulo      ──>  02-libro.md
            ├─ skill generar-ejercicios ──> 03-ejercicios.md
            ├─ skill generar-diapositivas ─> 05-diapositivas.md
            └─ skill edicion-docente    ──> 04-docente.md
                 └─ build/scripts/construir_*.py ──> salidas/ (PDF, PPTX)
```

## Comandos

```bash
python3 build/scripts/ingerir_fuentes.py contenido/fuentes/*.pptx --capitulo cap01 --docente "Nombre"
python3 build/scripts/construir_libro.py --capitulo cap01                 # libro del productor
python3 build/scripts/construir_libro.py --capitulo cap01 --edicion docente  # edicion docente
python3 build/scripts/construir_presentacion.py --capitulo cap01
python3 build/scripts/verificar_sync.py --capitulo cap01     # libro ↔ presentación
```

## Reglas del proyecto

- **Colores, tipografía y espaciado viven solo en `diseno/css/tokens.css`.** Usar `var(--bc-*)`;
  no introducir valores literales en otras hojas de estilo.
- **El formato de contenido está fijado en `contenido/ESQUEMA.md`.** Los bloques `:::nombre`
  son el contrato entre el contenido y los motores de maquetación.
- **No inventar datos técnicos.** Dosis, concentraciones, cepas comerciales y precios solo
  pueden salir de `01-fuente.md`. Si falta un dato, dejar
  `<!-- FALTA: confirmar con el docente -->` en su lugar. Un productor puede actuar sobre
  una cifra equivocada: este es el riesgo más serio del proyecto.
- **El contenido de muestra se marca `[MUESTRA]`** y no se atribuye a ningún docente.
- Cada capítulo declara en `meta.yaml` el docente que aportó el material.

## Docentes y módulos

| Módulo | Tema | Docente |
|---|---|---|
| cap01 | Biofertilización y micorrizas | *(por asignar)* |
| cap02 | Material de siembra élite y semilla artificial | *(por asignar)* |
| cap03 | Monitoreo y control de insectos en agricultura | *(por asignar)* |
| cap04 | Biocontrol de enfermedades y salud de suelo | *(por asignar)* |
| cap05 | Tratamientos poscosecha | *(por asignar)* |

Aportan material: William Watson, William Rivera, Randall Sequeira, Luis Barbosa.
