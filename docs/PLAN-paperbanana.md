# Plan: PaperBanana + Three.js

**Estado:** aprobado, pendiente de ejecutar **después de la entrega de los capítulos**.
**Decisiones tomadas:** instalación en `tools/PaperBanana/` ignorada por git (no submódulo).

PaperBanana (https://github.com/dwzhu-pku/PaperBanana) genera diagramas
estáticos con una cadena de agentes Retriever → Planner → Stylist → Visualizer
→ Critic. No anima: la animación la haría este proyecto con Three.js, usando el
plan textual de PaperBanana como guía.

## Hallazgos de la inspección previa (hecha el 2026-11-11)

Esto ya está verificado; no hace falta volver a averiguarlo.

- **`skill/run.py` NO expone el plan textual.** Guarda solo el PNG. Pero el
  `result` interno del pipeline sí trae la descripción, bajo claves con la
  forma `target_{task}_stylist_desc0_base64_jpg` (ver `run.py` líneas ~253-260),
  con respaldo al Planner cuando no hay Stylist. **Por eso hace falta el
  envoltorio**: llamar al pipeline directamente y volcar esas claves a JSON, sin
  tocar el repo de terceros.
- Argumentos reales de `run.py`: `--content` / `--content-file`, `--caption`,
  `--task diagram`, `--output`, `--aspect-ratio` (21:9 | 16:9 | 3:2),
  `--max-critic-rounds`, `--num-candidates`, `--exp-mode`
  (`demo_full` | `demo_planner_critic`), `--planner-metaphor`.
- Requiere **Python 3.12** (nuestro contenedor trae 3.13; `uv` resuelve 3.12).
- Claves: `OPENROUTER_API_KEY` (preferida, cubre texto e imagen) o
  `GOOGLE_API_KEY`. **Van por variable de entorno o por el formulario seguro de
  credenciales. Nunca en el código ni en el repositorio.**
- Este proyecto **no tiene `package.json`**: Three.js sería el primer toolchain
  JS. Node v22 está disponible.

## Fases

1. **Instalación aislada.** `tools/PaperBanana/` (en `.gitignore`), entorno `uv`
   con Python 3.12, `uv pip install -r requirements.txt`,
   `python scripts/prepare_bench.py --tasks diagram`.
2. **Envoltorio** `build/scripts/paperbanana_wrap.py`: ejecuta el pipeline,
   guarda el PNG y vuelca el plan de Planner/Stylist a JSON.
3. **Escena estructurada:** `plan.json → escena.json` con
   `{nodes:[{id,label,group,color,position}], edges:[{from,to,label}],
   steps:[{order,highlight,caption}]}`, usando el PNG como referencia de paleta
   y disposición.
4. **Animación Three.js** en `visor/`: nodos como mallas con etiquetas
   (CSS2DRenderer), conexiones con flujo animado, cámara recorriendo los
   `steps`, controles play/pausa y paso siguiente/anterior, OrbitControls
   opcional. Opcional: exportar a vídeo con MediaRecorder.

## Riesgos que hay que mirar antes de integrar

1. **El estilo puede no pegar.** PaperBanana está afinado para figuras de
   artículos académicos (NeurIPS, ICML, ACL). Este libro es escolar, para
   productores. **Probar con UNA figura antes de integrarlo al pipeline.**
2. **La animación no cabe en los entregables actuales.** Libro y edición docente
   son PDF; la presentación exporta a PPTX y PDF. Los tres son estáticos. La
   animación sería un **cuarto entregable**: un HTML que el expositor abre en el
   navegador durante la charla.
3. **Las figuras actuales ya funcionan.** `build/scripts/generar_figuras.py`
   dibuja SVG vectorial por ramificación recursiva con semilla fija: imprime
   nítido a cualquier tamaño, pesa poco y se edita por código. PaperBanana tiene
   que superar eso para ganarse el lugar, no solo funcionar.
