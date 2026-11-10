# Guía visual — razón de cada decisión

## Paleta

| Token | Color | Por qué |
|---|---|---|
| `--bc-verde-700` `#14633F` | verde biocontrol | Primario. Verde profundo, no "verde eco" saturado: en impresión a 4 tintas el verde brillante se ve barato y vibra contra el texto. |
| `--bc-tierra-500` `#D08A2C` | ocre suelo | Secundario cálido. Es el color del suelo y del sustrato: ancla el tema sin competir con el verde. Sirve para los bloques de **Ejemplo** (caso de campo). |
| `--bc-agua-500` `#2B7A9B` | azul agua | Terciario frío, para **Nota** y datos. Da el tercer eje que un libro escolar necesita para que el lector distinguga tipos de caja de un vistazo. |
| `--bc-alerta-600` `#B3432B` | terracota alerta | Solo para **Precaución**: dosis, incompatibilidades, fitotoxicidad. Rojo apagado, no señal de tránsito. |
| `--bc-papel` `#FAF7F0` | crema | Fondo de página. El blanco puro cansa y delata "documento impreso de oficina"; el crema lee como libro. |
| `--bc-tinta` `#1A2420` | tinta verdosa | Negro con una gota de verde, para que el texto pertenezca a la familia. |

Tres colores de acento y uno de alarma es el máximo antes de que el lector
pierda el código. Si aparece un sexto tipo de bloque, reutiliza un color
existente con otro icono, no agregues color.

## Tipografía

- **Bitter** (serif de contraste bajo) para titulares: tiene la personalidad de
  libro de texto y aguanta cuerpos grandes sin verse decorativa.
- **Source Sans 3** para cuerpo: diseñada para texto largo en pantalla e
  impresión, con números tabulares — importante en tablas de dosis.
- Cuerpo a 11 pt / interlínea 1.55: el público son productores, muchos leyendo
  en condiciones de campo. No bajar de 11 pt.

## Retícula

Márgenes asimétricos (interior 22 mm, exterior 16 mm) porque el libro se
imprime a doble cara y se engrapa o anilla: el lomo se come milímetros.

## Sobre LaTeX

Se evaluó y se descartó: LaTeX es excelente para artículos y fórmulas, pero
aquí el entregable manda cajas de color, figuras a sangre y un .pptx hermano.
HTML + CSS paginado (`@page`) resuelve eso y comparte la hoja de estilo con la
presentación, que es lo que mantiene libro y diapositivas visualmente idénticos.
Si en algún capítulo aparecen fórmulas, se renderizan con KaTeX dentro del HTML.
