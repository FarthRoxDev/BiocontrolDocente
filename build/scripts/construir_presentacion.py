#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construir_presentacion.py — BIOCONTROL
Markdown  ->  HTML slides 16:9  ->  PDF (Chromium)  ->  PPTX (python-pptx)

Uso:
    python3 build/scripts/construir_presentacion.py --capitulo cap01
    python3 build/scripts/construir_presentacion.py --entrada mazo.md --slug prueba
    python3 build/scripts/construir_presentacion.py --capitulo cap01 --texto-editable

Entrada: contenido/capitulos/capNN/05-diapositivas.md
    Un documento = varias diapositivas. Cada una arranca con front-matter YAML
    entre lineas `---`:

        ---
        slide: 3
        pagina: 12
        titulo: "Tipos de biofertilizantes"
        layout: vinetas        # portada|vinetas|columnas|imagen|dato|cierre
        notas: |
          Guion del expositor (va al panel de notas del .pptx).
        ---
        - Primera viñeta
        - Segunda viñeta

    En `layout: columnas` el cuerpo se parte con una linea `+++`.
    Las notas tambien pueden escribirse en el cuerpo como bloque
    `:::notas ... :::`.

Salidas: salidas/presentacion/capNN.html / .pdf / .pptx
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

try:
    import markdown as _markdown
except Exception:  # pragma: no cover - fallback minimo
    _markdown = None

RAIZ = Path(__file__).resolve().parents[2]
DIR_PLANTILLAS = RAIZ / "plantillas" / "presentacion"
CSS_TOKENS = RAIZ / "diseno" / "css" / "tokens.css"
CSS_PRESENTACION = RAIZ / "diseno" / "css" / "presentacion.css"
DIR_SALIDA = RAIZ / "salidas" / "presentacion"

LAYOUTS = ("portada", "vinetas", "columnas", "imagen", "dato", "cierre", "tabla")
# Alias: los mazos del equipo de contenido nombran los layouts a su manera.
ALIAS_LAYOUT = {
    "titulo-contenido": "vinetas", "titulo+vinetas": "vinetas", "vinetas": "vinetas",
    "contenido": "vinetas", "lista": "vinetas",
    "dos-columnas": "columnas", "comparacion": "columnas", "columnas": "columnas",
    "imagen-texto": "vinetas",          # sin `imagen:` es texto; con imagen pasa a sangre
    "imagen-sangre": "imagen", "foto": "imagen", "imagen": "imagen",
    "cita": "dato", "numero": "dato", "dato": "dato",
    "cierre-seccion": "cierre", "resumen": "cierre", "cierre": "cierre",
    "portada": "portada", "tabla": "tabla",
}
CLAVES_FM = {
    "slide", "pagina", "titulo", "layout", "kicker", "subtitulo", "notas",
    "imagen", "pie", "dato", "cita", "fuente", "meta", "seccion",
}
UMBRAL_PALABRAS = 40

# Lienzo CSS: 1280 x 720 "pt" de maquetacion (16:9 exacto), como pide @page.
SLIDE_PT = (1280, 720)
SLIDE_IN = (SLIDE_PT[0] / 72.0, SLIDE_PT[1] / 72.0)              # 17.778 x 10 in (PDF)
SLIDE_PX = (round(SLIDE_PT[0] * 96 / 72), round(SLIDE_PT[1] * 96 / 72))  # 1707 x 960 px
# Lienzo PPTX: el 16:9 estandar de PowerPoint. Misma proporcion, otro tamaño
# fisico, asi que la maquetacion nativa se escala por ESCALA_PPTX.
PPTX_IN = (13.3333, 7.5)
ESCALA_PPTX = PPTX_IN[0] / SLIDE_IN[0]   # 0.75 : 1 pt del CSS -> 0.75 pt reales


# ----------------------------------------------------------------- utilidades
def aviso(msg: str) -> None:
    print(f"  [AVISO] {msg}", file=sys.stderr)


def error_claro(msg: str, codigo: int = 1) -> "None":
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(codigo)


def md_inline(texto: str) -> str:
    """Markdown en una linea -> HTML sin <p> envolvente."""
    texto = texto.strip()
    if not texto:
        return ""
    if _markdown is not None:
        salida = _markdown.markdown(texto, output_format="html").strip()
    else:
        salida = "<p>" + html_mod.escape(texto) + "</p>"
        salida = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", salida)
        salida = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", salida)
    if salida.startswith("<p>") and salida.endswith("</p>") and salida.count("<p>") == 1:
        salida = salida[3:-4]
    return salida


def md_bloque(texto: str) -> str:
    """Markdown de varios parrafos -> HTML."""
    texto = texto.strip()
    if not texto:
        return ""
    if _markdown is not None:
        return _markdown.markdown(texto, extensions=["tables"], output_format="html").strip()
    return "".join(f"<p>{html_mod.escape(p.strip())}</p>" for p in re.split(r"\n\s*\n", texto))


def sin_etiquetas(html_txt: str) -> str:
    return re.sub(r"<[^>]+>", " ", html_txt or "")


def html_a_lineas(html_txt: str, vineta: str = "\u2022 ") -> str:
    """HTML de cuerpo -> texto plano por lineas, conservando las viñetas.
    Solo lo usa la ruta --texto-editable (python-pptx no entiende HTML)."""
    if not html_txt:
        return ""
    texto = re.sub(r"(?i)<li[^>]*>", "\n" + vineta, html_txt)
    texto = re.sub(r"(?i)</(p|div|h[1-6]|ul|ol|li|tr)>", "\n", texto)
    texto = re.sub(r"(?i)<br\s*/?>", "\n", texto)
    texto = html_mod.unescape(sin_etiquetas(texto))
    lineas = [re.sub(r"[ \t]+", " ", l).strip() for l in texto.split("\n")]
    return "\n".join(l for l in lineas if l and l != vineta.strip())


def contar_palabras(*trozos: str) -> int:
    texto = " ".join(sin_etiquetas(t) for t in trozos if t)
    texto = html_mod.unescape(texto)
    return len([p for p in re.split(r"\s+", texto) if re.search(r"\w", p, re.UNICODE)])


# -------------------------------------------------------------------- parseo
@dataclass
class Slide:
    slide: int = 0
    pagina: "int | None" = None
    titulo: str = ""
    layout: str = "vinetas"
    kicker: str = ""
    subtitulo: str = ""
    seccion: str = ""
    imagen: str = ""          # URI lista para el HTML
    imagen_path: str = ""     # ruta local absoluta (si existe)
    pie: str = ""
    dato: str = ""
    cita: str = ""
    fuente: str = ""
    meta: str = ""
    notas: str = ""
    html: str = ""
    vinetas: list = field(default_factory=list)
    columnas: list = field(default_factory=list)
    titulo_html: str = ""
    intro: str = ""
    palabras: int = 0
    denso: bool = False


def separar_bloques(texto: str):
    """Devuelve [(front_matter_dict, cuerpo_str), ...].

    El documento se corta por lineas que son exactamente `---`. Un trozo se
    considera front-matter si es un mapping YAML con al menos una clave
    conocida; cualquier otro trozo es cuerpo de la diapositiva en curso.
    """
    trozos = re.split(r"(?m)^[ \t]*---[ \t]*$\n?", texto)
    bloques = []
    pendiente = None
    for trozo in trozos:
        if not trozo.strip():
            continue
        fm = None
        try:
            cargado = yaml.safe_load(trozo)
            if isinstance(cargado, dict) and (set(cargado) & CLAVES_FM):
                fm = cargado
        except yaml.YAMLError:
            fm = None
        if fm is not None:
            if pendiente is not None:
                bloques.append((pendiente, ""))
            pendiente = fm
        else:
            if pendiente is None:
                # Un comentario HTML de cabecera es normal; cualquier otra cosa, no.
                if re.sub(r"(?s)<!--.*?-->", "", trozo).strip():
                    aviso("se ignora texto previo al primer front-matter")
                continue
            bloques.append((pendiente, trozo))
            pendiente = None
    if pendiente is not None:
        bloques.append((pendiente, ""))
    return bloques


def extraer_notas(cuerpo: str):
    """Saca bloques `:::notas ... :::` del cuerpo."""
    notas = []

    def _sacar(m):
        notas.append(m.group(1).strip())
        return ""

    cuerpo = re.sub(r"(?ms)^:::notas[ \t]*\n(.*?)^:::[ \t]*$\n?", _sacar, cuerpo)
    return cuerpo, "\n\n".join(notas)


def quitar_h1(cuerpo: str):
    """Saca el primer `# Titulo` del cuerpo (los mazos lo repiten del
    front-matter) y lo devuelve por separado."""
    m = re.match(r"(?s)\s*#\s+(.+?)\s*(?:\n|$)", cuerpo)
    if not m:
        return cuerpo, ""
    return cuerpo[m.end():], m.group(1).strip()


def _clasear(html_txt: str) -> str:
    """Marca las listas de primer nivel con la clase de viñetas del CSS."""
    html_txt = re.sub(r"(?i)<ul>", '<ul class="bc-lista">', html_txt)
    html_txt = re.sub(r"(?i)<ol>", '<ol class="bc-lista bc-lista--num">', html_txt)
    # las anidadas vuelven a quedar sin clase
    html_txt = re.sub(r'(?i)(<li[^>]*>(?:(?!</li>).)*?)<ul class="bc-lista">',
                      r"\1<ul>", html_txt)
    return html_txt


def normalizar_sangria(cuerpo: str) -> str:
    """Las sublistas se escriben con 2 espacios; python-markdown pide 4.
    Reindenta solo las lineas que empiezan con marca de lista."""
    salida = []
    for linea in cuerpo.split("\n"):
        m = re.match(r"^([ \t]+)([-*+]|\d+[.)])\s+", linea)
        if m:
            nivel = len(m.group(1).replace("\t", "  ")) // 2
            linea = " " * (4 * nivel) + linea.lstrip()
        salida.append(linea)
    return "\n".join(salida)


def parsear_cuerpo(cuerpo: str):
    """Cuerpo markdown -> (lista_de_vinetas, html_en_orden_de_documento).

    El HTML conserva el orden original (parrafos, subtitulos, listas,
    tablas y citas intercalados). La lista de viñetas se devuelve aparte
    solo como dato (conteo y ruta --texto-editable).
    """
    cuerpo = cuerpo.strip("\n")
    if not cuerpo.strip():
        return [], ""
    html_txt = _clasear(md_bloque(normalizar_sangria(cuerpo)))
    vinetas = [m.group(1).strip() for m in
               re.finditer(r"(?is)<li[^>]*>(.*?)</li>", html_txt)]
    return vinetas, html_txt


def construir_slides(texto: str, umbral: int, base_dir: Path) -> list:
    slides = []
    for idx, (fm, cuerpo) in enumerate(separar_bloques(texto), start=1):
        s = Slide()
        s.slide = int(fm.get("slide") or idx)
        pagina = fm.get("pagina", None)
        if pagina is not None and str(pagina).strip() != "":
            try:
                s.pagina = int(str(pagina).strip())
            except ValueError:
                aviso(f"diapositiva {s.slide}: `pagina: {pagina!r}` no es un entero; se ignora")
        else:
            aviso(f"diapositiva {s.slide}: sin `pagina:` — se pierde la sincronia con el libro")
        s.titulo = str(fm.get("titulo") or "").strip()
        crudo_layout = str(fm.get("layout") or "vinetas").strip().lower()
        s.layout = ALIAS_LAYOUT.get(crudo_layout, crudo_layout)
        if s.layout not in LAYOUTS:
            aviso(f"diapositiva {s.slide}: layout '{crudo_layout}' desconocido; se usa 'vinetas'")
            s.layout = "vinetas"
        for clave in ("kicker", "subtitulo", "seccion", "imagen", "pie",
                      "dato", "cita", "fuente", "meta"):
            setattr(s, clave, str(fm.get(clave) or "").strip())
        s.notas = str(fm.get("notas") or "").strip()

        # Las imagenes del mazo se resuelven relativas al .md y se pasan al
        # HTML como file:// para que Chromium las cargue desde cualquier CWD.
        if s.imagen and not re.match(r"^(https?:|data:|file:)", s.imagen):
            ruta_img = (base_dir / s.imagen).resolve()
            if ruta_img.exists():
                s.imagen_path = str(ruta_img)
                s.imagen = ruta_img.as_uri()
            else:
                aviso(f"diapositiva {s.slide}: no existe la imagen {ruta_img}")
                s.imagen = ""
        elif s.imagen.startswith("file:"):
            s.imagen_path = s.imagen[7:]

        cuerpo, notas_cuerpo = extraer_notas(cuerpo or "")
        if notas_cuerpo:
            s.notas = (s.notas + "\n\n" + notas_cuerpo).strip()

        # El cuerpo suele repetir el titulo como `# ...`: lo sacamos.
        cuerpo, h1 = quitar_h1(cuerpo)
        if h1 and not s.titulo:
            s.titulo = re.sub(r"[*_`]", "", h1).strip()
        s.titulo_html = md_inline(h1) if h1 else html_mod.escape(s.titulo)
        if crudo_layout in ("imagen-texto", "imagen-sangre", "foto") and s.imagen:
            s.layout = "imagen"

        if s.layout == "columnas":
            partes = re.split(r"(?m)^[ \t]*\+\+\+[ \t]*$\n?", cuerpo)
            if len(partes) == 1:
                # Sin `+++`: se parte por los subtitulos `###` (uso real del equipo)
                trozos = re.split(r"(?m)^[ \t]*#{2,3}[ \t]+(.+?)[ \t]*$\n?", cuerpo)
                if len(trozos) >= 5:          # intro, t1, c1, t2, c2, ...
                    s.intro = md_bloque(trozos[0])
                    pares = [(trozos[i], trozos[i + 1]) for i in range(1, len(trozos) - 1, 2)]
                    for j, (tit, cont) in enumerate(pares):
                        destino = min(j, 1)
                        _, resto = parsear_cuerpo(cont)
                        bloque = (f"<h2>{md_inline(tit)}</h2>" if j > 1 else "") + resto
                        if destino < len(s.columnas):
                            s.columnas[destino]["html"] += bloque
                        else:
                            s.columnas.append({"titulo": md_inline(tit), "html": resto})
                    while len(s.columnas) < 2:
                        s.columnas.append({"titulo": "", "html": ""})
                    partes = None
            if partes is not None and len(partes) == 1:
                aviso(f"diapositiva {s.slide}: layout 'columnas' sin '+++' ni dos "
                      "subtitulos '###'; todo el cuerpo va a la primera columna")
            for parte in (partes[:2] if partes and len(partes) > 2 else (partes or [])):
                titulo_col = ""
                m = re.match(r"(?m)^\s*#{1,3}\s+(.+?)\s*$\n?", parte)
                if m:
                    titulo_col = m.group(1).strip()
                    parte = parte[m.end():]
                _, html_col = parsear_cuerpo(parte)
                s.columnas.append({"titulo": titulo_col, "html": html_col})
            if partes and len(partes) > 2:
                aviso(f"diapositiva {s.slide}: layout 'columnas' con {len(partes)} bloques; "
                      "solo se usan los dos primeros")
            while len(s.columnas) < 2:
                s.columnas.append({"titulo": "", "html": ""})
        else:
            s.vinetas, s.html = parsear_cuerpo(cuerpo)

        textos = [s.titulo, s.subtitulo, s.intro, s.html, s.dato, s.cita, s.pie,
                  s.fuente, s.meta, s.kicker]
        textos += [c["titulo"] + " " + c["html"] for c in s.columnas]
        s.palabras = contar_palabras(*textos)
        s.denso = s.palabras > umbral
        slides.append(s)
    return slides


# -------------------------------------------------------------------- render
def render_html(slides: list, capitulo: str, titulo_mazo: str,
                avisos_visibles: bool) -> str:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader(str(DIR_PLANTILLAS)),
        autoescape=select_autoescape(enabled_extensions=("html",), default=False),
    )
    env.filters["safe_html"] = lambda v: v
    plantilla = env.get_template("mazo.html")
    # `html`, `vinetas` y `columnas[].html` ya son HTML: los marcamos.
    from markupsafe import Markup

    ctx_slides = []
    for s in slides:
        d = dict(s.__dict__)
        d["html"] = Markup(d["html"] or "")
        d["intro"] = Markup(d["intro"] or "")
        d["titulo_html"] = Markup(d["titulo_html"] or html_mod.escape(d["titulo"]))
        d["vinetas"] = [Markup(v) for v in d["vinetas"]]
        d["columnas"] = [{"titulo": c["titulo"], "html": Markup(c["html"])} for c in d["columnas"]]
        ctx_slides.append(d)
    return plantilla.render(
        slides=ctx_slides,
        total=len(slides),
        capitulo=capitulo,
        titulo_mazo=titulo_mazo,
        css_tokens=CSS_TOKENS.resolve().as_uri(),
        css_presentacion=CSS_PRESENTACION.resolve().as_uri(),
        avisos_visibles=avisos_visibles,
    )


def _chromium(p):
    """Chromium de Playwright, o el Chrome del sistema si no hay descarga."""
    intentos = [
        dict(),
        dict(channel="chrome"),
        dict(executable_path="/usr/bin/google-chrome"),
    ]
    ultimo = None
    for kw in intentos:
        try:
            return p.chromium.launch(args=["--no-sandbox", "--font-render-hinting=none"], **kw)
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
    error_claro(f"no se pudo abrir Chromium para exportar: {ultimo}")


def exportar_pdf_y_pngs(ruta_html: Path, ruta_pdf: Path, dir_png: Path, n_slides: int):
    """PDF vectorial + un PNG por diapositiva (deviceScaleFactor 2)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        error_claro("falta Playwright (pip install playwright && playwright install chromium)")

    pngs = []
    with sync_playwright() as p:
        navegador = _chromium(p)
        try:
            ctx = navegador.new_context(
                viewport={"width": SLIDE_PX[0], "height": SLIDE_PX[1]},
                device_scale_factor=2,
            )
            pagina = ctx.new_page()
            pagina.goto(ruta_html.resolve().as_uri(), wait_until="load")
            pagina.emulate_media(media="print")
            pagina.pdf(
                path=str(ruta_pdf),
                prefer_css_page_size=True,          # respeta @page size:1280pt 720pt
                width=f"{SLIDE_IN[0]}in",
                height=f"{SLIDE_IN[1]}in",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            pagina.emulate_media(media="screen")
            dir_png.mkdir(parents=True, exist_ok=True)
            for i in range(1, n_slides + 1):
                el = pagina.query_selector(f"#slide-{i}")
                if el is None:
                    continue
                destino = dir_png / f"slide-{i:02d}.png"
                el.screenshot(path=str(destino))
                pngs.append(destino)
            ctx.close()
        finally:
            navegador.close()
    return pngs


# ---------------------------------------------------------------------- pptx
def cargar_tokens() -> dict:
    """Lee los colores --bc-* de tokens.css: fuente unica de verdad.

    Asi el .pptx con texto nativo usa exactamente la misma paleta que el CSS
    y no se inventa ningun color en este script.
    """
    texto = CSS_TOKENS.read_text(encoding="utf-8")
    # Solo el bloque :root base: el override de @media dark no aplica al PPTX.
    corte = texto.find("@media")
    if corte > 0:
        texto = texto[:corte]
    return {
        f"--{n}": v.strip()
        for n, v in re.findall(r"--(bc-[a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{3,8})\s*;", texto)
    }


def rgb(tokens: dict, nombre: str):
    from pptx.dml.color import RGBColor

    valor = tokens.get(nombre)
    if not valor:
        error_claro(f"el token de color {nombre} no existe en tokens.css")
    return RGBColor.from_string(valor.lstrip("#").upper())


def construir_pptx(slides: list, pngs: list, ruta_pptx: Path, texto_editable: bool):
    """Genera el .pptx 13.333 x 7.5 in.

    ─── TRADE-OFF (leer antes de cambiar nada) ────────────────────────────
    Hay dos maneras de llevar estas diapositivas a PowerPoint y no son
    equivalentes:

    1) RUTA POR DEFECTO — imagen fiel.
       Rasterizamos cada slide del HTML con Playwright (deviceScaleFactor 2)
       y pegamos el PNG a sangre completa. Se ve EXACTAMENTE igual que el PDF:
       misma tipografia, mismo indicador "Libro pag. N", mismos layouts,
       sin depender de que PowerPoint tenga las fuentes Bitter / Source Sans 3.
       El costo: el texto del cuerpo no es editable ni seleccionable, y no
       hay accesibilidad de texto sobre la imagen. Para compensar, las notas
       del expositor SI se escriben como texto real en el notes_slide, que es
       lo que el expositor necesita editar en el momento.

    2) RUTA --texto-editable — cajas nativas.
       Construimos cada slide con shapes y text frames de python-pptx. El
       texto se edita y se busca, pero la fidelidad baja: PowerPoint rehace
       el salto de linea, sustituye fuentes que no tenga instaladas y no
       reproduce gradientes, imagenes a sangre ni el detalle fino del CSS.
       Pensada para que el docente reescriba contenido, no para proyectar.

    Por eso la fidelidad es el default y la editabilidad es una bandera
    explicita: el uso normal es proyectar, no editar.
    ───────────────────────────────────────────────────────────────────────
    """
    from pptx import Presentation
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width = Inches(PPTX_IN[0])     # 13.333 in  (16:9 estandar)
    prs.slide_height = Inches(PPTX_IN[1])    # 7.5 in
    layout_vacio = prs.slide_layouts[6]      # blank

    tokens = cargar_tokens()

    for i, s in enumerate(slides):
        diap = prs.slides.add_slide(layout_vacio)
        if texto_editable:
            _pptx_nativo(prs, diap, s, tokens)
        else:
            png = pngs[i] if i < len(pngs) else None
            if png is None or not Path(png).exists():
                aviso(f"diapositiva {s.slide}: sin PNG rasterizado; queda en blanco")
            else:
                diap.shapes.add_picture(
                    str(png), 0, 0,
                    width=prs.slide_width, height=prs.slide_height,
                )
        # Notas del expositor como TEXTO REAL y editable en ambas rutas.
        partes = []
        if s.pagina is not None:
            partes.append(f"Libro pag. {s.pagina}")
        if s.notas:
            partes.append(s.notas)
        partes.append(f"[diapositiva {s.slide} · layout {s.layout} · {s.palabras} palabras]")
        diap.notes_slide.notes_text_frame.text = "\n\n".join(partes)

    ruta_pptx.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(ruta_pptx))


def _pptx_nativo(prs, diap, s, tokens):
    """Ruta --texto-editable: cajas de texto nativas de python-pptx.

    La geometria se escribe en las mismas unidades que el CSS (lienzo de
    1280x720) y se convierte al lienzo real con U / PT: asi los dos caminos
    comparten numeros y cambiar el tamaño del .pptx no descoloca nada.
    """
    from pptx.util import Inches, Pt, Emu
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE

    W, H = prs.slide_width, prs.slide_height
    U = W / SLIDE_PT[0]                     # EMU por "pt del CSS"

    def u(v):                               # pt del CSS -> EMU
        return Emu(int(round(v * U)))

    def pt(v):                              # pt del CSS -> puntos tipograficos
        return Pt(round(v * ESCALA_PPTX, 1))

    MX, MY = u(76), u(56)
    ANCHO = W - 2 * MX

    fondos = {
        "portada": ("--bc-verde-900", "--bc-papel"),
        "cierre": ("--bc-verde-700", "--bc-papel"),
        "dato": ("--bc-verde-100", "--bc-verde-900"),
        "imagen": ("--bc-verde-900", "--bc-papel"),
    }
    tk_fondo, tk_texto = fondos.get(s.layout, ("--bc-papel", "--bc-tinta"))
    fondo = diap.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    fondo.fill.solid()
    fondo.fill.fore_color.rgb = rgb(tokens, tk_fondo)
    fondo.line.fill.background()
    fondo.shadow.inherit = False

    def caja(x, y, w, h, texto, tam, color, negrita=False, fuente=None,
             alineacion=PP_ALIGN.LEFT, espaciado=1.2):
        tb = diap.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        for j, linea in enumerate(str(texto).split("\n")):
            par = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
            par.alignment = alineacion
            par.line_spacing = espaciado
            run = par.add_run()
            run.text = linea
            run.font.size = pt(tam)
            run.font.bold = negrita
            run.font.color.rgb = rgb(tokens, color)
            run.font.name = fuente or "Source Sans 3"
        return tb

    y = MY
    if s.kicker:
        caja(MX, y, ANCHO, u(30), s.kicker.upper(), 22,
             "--bc-tierra-100" if s.layout == "cierre" else "--bc-tierra-500", True)
        y += u(40)

    if s.layout == "portada":
        caja(MX, y, ANCHO, u(190), s.titulo, 76, "--bc-papel", True,
             fuente="Bitter", espaciado=1.05)
        y += u(170)
        if s.subtitulo:
            caja(MX, y, ANCHO, u(70), s.subtitulo, 28, "--bc-verde-100")
            y += u(70)
        if s.meta:
            caja(MX, H - u(90), ANCHO, u(36), s.meta, 20, "--bc-verde-400")

    elif s.layout == "dato":
        if s.dato:
            caja(MX, y, ANCHO, u(140), s.dato, 110, "--bc-verde-700", True,
                 fuente="Bitter", espaciado=1.0)
            y += u(145)
        texto_cita = s.cita or s.titulo
        if texto_cita:
            caja(MX, y, ANCHO, u(170), texto_cita, 44, "--bc-verde-900", False,
                 fuente="Bitter", espaciado=1.24)
        if s.fuente:
            caja(MX, H - u(100), ANCHO, u(36), s.fuente, 20, "--bc-tinta-suave")

    elif s.layout == "imagen":
        if s.imagen_path and Path(s.imagen_path).exists():
            diap.shapes.add_picture(s.imagen_path, 0, 0, width=W, height=H)
        if s.titulo:
            caja(MX, MY, ANCHO, u(80), s.titulo, 48, "--bc-papel", True, fuente="Bitter")
        if s.pie:
            caja(MX, H - u(150), ANCHO - u(280), u(80), s.pie, 28, "--bc-papel")

    elif s.layout == "columnas":
        caja(MX, y, ANCHO, u(60), s.titulo, 48, "--bc-verde-900", True, fuente="Bitter")
        y += u(86)
        if s.intro:
            intro = html_a_lineas(s.intro)
            if intro:
                caja(MX, y, ANCHO, u(60), intro, 24, tk_texto)
                y += u(60)
        gap = u(46)
        ancho_col = (ANCHO - gap) // 2
        for k, col in enumerate(s.columnas[:2]):
            x = MX + k * (ancho_col + gap)
            yy = y
            if col["titulo"]:
                caja(x, yy, ancho_col, u(44), html_a_lineas(col["titulo"]) or col["titulo"],
                     32, "--bc-agua-700", True, fuente="Bitter")
                yy += u(52)
            texto = html_a_lineas(col["html"])
            if texto:
                caja(x, yy, ancho_col, H - yy - u(70), texto, 26, tk_texto, espaciado=1.3)

    else:  # vinetas / tabla / cierre
        caja(MX, y, ANCHO, u(70), s.titulo, 48,
             "--bc-papel" if s.layout == "cierre" else "--bc-verde-900",
             True, fuente="Bitter")
        y += u(100)
        cuerpo = html_a_lineas(s.html, vineta="\u2022 ")
        if cuerpo:
            caja(MX, y, ANCHO, H - y - u(80), cuerpo, 28,
                 "--bc-verde-100" if s.layout == "cierre" else "--bc-tinta",
                 espaciado=1.35)

    # Indicador de pagina del libro (misma funcion que en el CSS)
    if s.pagina is not None:
        ancho, alto = u(166), u(38)
        chip = diap.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                     W - MX - ancho, H - u(64), ancho, alto)
        chip.fill.solid()
        claro = s.layout in ("portada", "cierre", "imagen")
        chip.fill.fore_color.rgb = rgb(tokens, "--bc-papel" if claro else "--bc-verde-700")
        chip.line.fill.background()
        chip.shadow.inherit = False
        par = chip.text_frame.paragraphs[0]
        par.alignment = PP_ALIGN.CENTER
        run = par.add_run()
        run.text = f"Libro pag. {s.pagina}"
        run.font.size = pt(21)
        run.font.bold = True
        run.font.name = "Source Sans 3"
        run.font.color.rgb = rgb(tokens, "--bc-verde-900" if claro else "--bc-papel")


# ----------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Construye la presentacion 16:9 de un capitulo (HTML -> PDF -> PPTX).")
    ap.add_argument("--capitulo", help="p.ej. cap01 (lee contenido/capitulos/cap01/05-diapositivas.md)")
    ap.add_argument("--entrada", help="ruta explicita a un .md de diapositivas")
    ap.add_argument("--slug", help="nombre base de las salidas si se usa --entrada")
    ap.add_argument("--salida", help="directorio de salida (default salidas/presentacion)")
    ap.add_argument("--texto-editable", action="store_true",
                    help="construye el .pptx con cajas de texto nativas en vez de PNG a sangre")
    ap.add_argument("--umbral-palabras", type=int, default=UMBRAL_PALABRAS,
                    help=f"palabras maximas por diapositiva antes de avisar (default {UMBRAL_PALABRAS})")
    ap.add_argument("--marcar-densas", action="store_true",
                    help="dibuja una banda roja en las diapositivas densas (solo revision)")
    ap.add_argument("--solo-html", action="store_true", help="no exporta PDF ni PPTX")
    args = ap.parse_args(argv)

    if not args.capitulo and not args.entrada:
        error_claro("indica --capitulo capNN o --entrada ruta/al.md")

    if args.capitulo:
        slug = args.capitulo
        entrada = RAIZ / "contenido" / "capitulos" / slug / "05-diapositivas.md"
    else:
        entrada = Path(args.entrada).expanduser().resolve()
        slug = args.slug or entrada.stem

    if not entrada.exists():
        error_claro(f"no existe el mazo de entrada: {entrada}\n"
                    "       (si el capitulo todavia no tiene 05-diapositivas.md, "
                    "usa --entrada con un mazo de prueba)", 2)

    dir_salida = Path(args.salida).expanduser().resolve() if args.salida else DIR_SALIDA
    dir_salida.mkdir(parents=True, exist_ok=True)

    print(f"Mazo: {entrada}")
    slides = construir_slides(entrada.read_text(encoding="utf-8"),
                              args.umbral_palabras, entrada.parent)
    if not slides:
        error_claro("el mazo no contiene ninguna diapositiva con front-matter YAML")
    print(f"Diapositivas: {len(slides)}")

    densas = [s for s in slides if s.denso]
    for s in densas:
        aviso(f"diapositiva {s.slide} ('{s.titulo or s.layout}') tiene {s.palabras} palabras "
              f"(> {args.umbral_palabras}): demasiado texto para proyectar, partila")
    if not densas:
        print(f"Densidad: OK, ninguna diapositiva supera {args.umbral_palabras} palabras")

    ruta_html = dir_salida / f"{slug}.html"
    ruta_html.write_text(
        render_html(slides, slug, f"BIOCONTROL — {slug}", args.marcar_densas),
        encoding="utf-8")
    print(f"HTML : {ruta_html}")
    if args.solo_html:
        return 0

    ruta_pdf = dir_salida / f"{slug}.pdf"
    dir_png = dir_salida / f"_png-{slug}"
    pngs = exportar_pdf_y_pngs(ruta_html, ruta_pdf, dir_png, len(slides))
    print(f"PDF  : {ruta_pdf}")
    if len(pngs) != len(slides) and not args.texto_editable:
        aviso(f"se rasterizaron {len(pngs)} de {len(slides)} diapositivas")

    ruta_pptx = dir_salida / f"{slug}.pptx"
    construir_pptx(slides, pngs, ruta_pptx, args.texto_editable)
    modo = "texto editable (cajas nativas)" if args.texto_editable else "imagen fiel (PNG a sangre)"
    print(f"PPTX : {ruta_pptx}  [{modo}, notas del expositor como texto real]")

    paginas = [s.pagina for s in slides if s.pagina is not None]
    if paginas:
        print(f"Sincronia: paginas del libro referenciadas {min(paginas)}–{max(paginas)} "
              f"({len(paginas)}/{len(slides)} diapositivas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
