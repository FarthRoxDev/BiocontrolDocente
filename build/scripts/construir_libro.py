#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construir_libro.py — motor de maquetación del libro de texto Biocontrol.

Markdown (con bloques didácticos ":::nombre{atributos}") → HTML paginado A4
→ PDF por Chromium/Playwright, más el mapa de páginas que consume
build/scripts/verificar-sync.py.

Uso:
    python3 build/scripts/construir_libro.py --capitulo cap01 [--salida salidas/libro]
    python3 build/scripts/construir_libro.py --capitulo cap01 --fuente /ruta/prueba-libro.md

Salidas (en --salida):
    capNN.html            HTML paginado (depurable en el navegador)
    capNN.pdf             PDF A4 con fondos, encabezado y pie corridos
    capNN-paginas.json    {"paginas": {"slug-del-heading": nº de página}, ...}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

try:
    import markdown as md_lib
except ImportError:  # pragma: no cover
    sys.exit("Falta el paquete 'markdown'. Instalar con: pip install markdown")

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup

# ----------------------------------------------------------------------
# Rutas del proyecto
# ----------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[2]
DIR_PLANTILLAS = RAIZ / "plantillas" / "libro"
CSS_TOKENS = RAIZ / "diseno" / "css" / "tokens.css"
CSS_LIBRO = RAIZ / "diseno" / "css" / "libro.css"

MM_A_PX = 96.0 / 25.4

# ----------------------------------------------------------------------
# Bloques didácticos (contrato de contenido/ESQUEMA.md)
# ----------------------------------------------------------------------
CAJAS = {
    "objetivos":  "Objetivos de aprendizaje",
    "nota":       "Nota",
    "ejemplo":    "Ejemplo de campo",
    "precaucion": "Precaución",
    "glosario":   "Glosario",
    "sabias-que": "¿Sabías que…?",
    "actividad":  "Actividad",
}
# Bloques que no se maquetan en el flujo del cuerpo sino que alimentan
# otras partes de la plantilla.
BLOQUES_APARTE = {"resumen", "ejercicio", "clave"}

RE_ABRE = re.compile(r"^:::[ \t]*([a-zA-Z][a-zA-Z0-9_-]*)[ \t]*(\{.*\})?[ \t]*$")
RE_CIERRA = re.compile(r"^:::[ \t]*$")
RE_ATRIBUTO = re.compile(
    r"""([A-Za-z_][\w-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s,}]+))"""
)


def parsear_atributos(crudo: str | None) -> dict:
    """`{src="a.png" pie="Pie" renglones=4}` → dict."""
    if not crudo:
        return {}
    atributos = {}
    for m in RE_ATRIBUTO.finditer(crudo):
        clave = m.group(1)
        valor = m.group(2) or m.group(3) or m.group(4) or ""
        atributos[clave] = valor
    return atributos


@dataclass
class Nodo:
    """Nodo del árbol del documento: texto markdown o bloque didáctico."""
    tipo: str                       # "texto" | nombre del bloque
    atributos: dict = field(default_factory=dict)
    lineas: list = field(default_factory=list)   # líneas de markdown
    hijos: list = field(default_factory=list)    # Nodo anidados


def parsear_bloques(texto: str) -> list[Nodo]:
    """Parser propio de contenedores de directiva `:::`, con anidamiento."""
    raiz = Nodo("raiz")
    pila = [raiz]

    def actual() -> Nodo:
        return pila[-1]

    def agregar_linea(linea: str) -> None:
        nodo = actual()
        if nodo.hijos and nodo.hijos[-1].tipo == "texto":
            nodo.hijos[-1].lineas.append(linea)
        else:
            nodo.hijos.append(Nodo("texto", lineas=[linea]))

    for linea in texto.splitlines():
        abre = RE_ABRE.match(linea)
        if abre:
            nuevo = Nodo(abre.group(1).lower(), parsear_atributos(abre.group(2)))
            actual().hijos.append(nuevo)
            pila.append(nuevo)
            continue
        if RE_CIERRA.match(linea) and len(pila) > 1:
            pila.pop()
            continue
        agregar_linea(linea)

    return raiz.hijos


# ----------------------------------------------------------------------
# Markdown → HTML
# ----------------------------------------------------------------------
def nuevo_md() -> "md_lib.Markdown":
    return md_lib.Markdown(
        extensions=["tables", "attr_list", "def_list", "sane_lists", "toc", "footnotes"],
        extension_configs={"toc": {"slugify": slug_es, "permalink": False}},
        output_format="html",
    )


def slug_es(valor: str, separador: str = "-") -> str:
    import unicodedata
    valor = unicodedata.normalize("NFKD", str(valor))
    valor = "".join(c for c in valor if not unicodedata.combining(c))
    valor = re.sub(r"[^\w\s-]", "", valor.lower())
    return re.sub(r"[\s_]+", separador, valor).strip(separador)


def lineas_de(nodo: Nodo) -> list[str]:
    """Líneas markdown directas de un bloque (el parser las guarda como
    hijos de tipo 'texto')."""
    salida: list[str] = []
    for hijo in nodo.hijos:
        if hijo.tipo == "texto":
            salida.extend(hijo.lineas)
    salida.extend(nodo.lineas)
    return salida


def md_a_html(lineas: list[str]) -> str:
    texto = "\n".join(lineas).strip("\n")
    if not texto.strip():
        return ""
    conv = nuevo_md()
    return conv.convert(texto)


def etiqueta_caja(nombre: str, atributos: dict) -> str:
    titulo = atributos.get("titulo") or CAJAS.get(nombre, nombre.replace("-", " ").title())
    return (
        '<p class="bc-caja__etiqueta">'
        '<span class="bc-caja__icono" aria-hidden="true"></span>'
        f"<span>{titulo}</span></p>"
    )


def render_figura(nodo: Nodo, dir_base: Path) -> str:
    src = nodo.atributos.get("src", "")
    pie = nodo.atributos.get("pie", "")
    alt = nodo.atributos.get("alt", pie)
    interno = md_a_html(lineas_de(nodo))

    ruta = (dir_base / src) if src else None
    if ruta and ruta.exists():
        visual = f'<img src="{ruta.resolve().as_uri()}" alt="{alt}">'
    elif src:
        visual = (
            f'<div class="bc-figura__hueco">Imagen pendiente: {src}</div>'
        )
    else:
        visual = '<div class="bc-figura__hueco">Espacio reservado para la figura</div>'

    cuerpo = [visual]
    if interno:
        cuerpo.append(interno)
    if pie:
        cuerpo.append(f'<figcaption class="bc-figura__pie">{pie}</figcaption>')
    return '<figure class="bc-figura">' + "".join(cuerpo) + "</figure>"


def render_tabla(nodo: Nodo) -> str:
    titulo = nodo.atributos.get("titulo", "")
    interno = md_a_html(lineas_de(nodo))
    cab = f'<p class="bc-tabla__titulo">{titulo}</p>' if titulo else ""
    return f'<div class="bc-tabla">{cab}{interno}</div>'


def render_nodos(nodos: list[Nodo], dir_base: Path, aparte: dict) -> str:
    """Devuelve el HTML del cuerpo y acumula en `aparte` los bloques
    que la plantilla maqueta por separado (resumen, ejercicios, clave)."""
    salida = []
    for nodo in nodos:
        if nodo.tipo == "texto":
            salida.append(md_a_html(nodo.lineas))
            continue

        if nodo.tipo in BLOQUES_APARTE:
            recolectar_aparte(nodo, aparte)
            continue

        if nodo.tipo == "figura":
            salida.append(render_figura(nodo, dir_base))
            continue

        if nodo.tipo == "tabla":
            salida.append(render_tabla(nodo))
            continue

        if nodo.tipo in CAJAS:
            interno = render_nodos(nodo.hijos, dir_base, aparte)
            salida.append(
                f'<aside class="bc-caja bc-caja--{nodo.tipo}">'
                f"{etiqueta_caja(nodo.tipo, nodo.atributos)}{interno}</aside>"
            )
            continue

        # Bloque desconocido: se maqueta como caja neutra y se avisa.
        print(f"  aviso: bloque ':::{nodo.tipo}' no reconocido, se usa caja neutra",
              file=sys.stderr)
        interno = render_nodos(nodo.hijos, dir_base, aparte)
        salida.append(f'<aside class="bc-caja">{etiqueta_caja(nodo.tipo, nodo.atributos)}{interno}</aside>')

    return "\n".join(h for h in salida if h.strip())


RE_ITEM_LISTA = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+(.*)$")


def items_de_lista(lineas: list[str]) -> list[str]:
    """Extrae los ítems de una lista markdown como HTML en línea (sin <p>)."""
    items, actual = [], None
    for linea in lineas:
        m = RE_ITEM_LISTA.match(linea)
        if m:
            if actual is not None:
                items.append(actual)
            actual = m.group(1).strip()
        elif linea.strip() and actual is not None:
            actual += " " + linea.strip()
        elif not linea.strip() and actual is not None:
            items.append(actual)
            actual = None
    if actual is not None:
        items.append(actual)

    conv = nuevo_md()
    salida = []
    for item in items:
        html = conv.reset().convert(item)
        html = re.sub(r"</?p>", "", html).strip()
        salida.append(Markup(html))
    return salida


def recolectar_aparte(nodo: Nodo, aparte: dict) -> None:
    if nodo.tipo == "resumen":
        aparte.setdefault("resumen", []).extend(items_de_lista(lineas_de(nodo)))
    elif nodo.tipo == "ejercicio":
        a = nodo.atributos
        aparte.setdefault("ejercicios", []).append({
            "enunciado_html": Markup(md_a_html(lineas_de(nodo))),
            "tipo": a.get("tipo", ""),
            "renglones": int(a.get("renglones", 3) or 0),
            "recuadro": a.get("recuadro", "").lower() in ("1", "si", "sí", "true"),
            "opciones": [Markup(o.strip()) for o in a.get("opciones", "").split("|") if o.strip()],
        })
    elif nodo.tipo == "clave":
        aparte.setdefault("clave", []).extend(
            {"respuesta_html": r} for r in items_de_lista(lineas_de(nodo))
        )


# ----------------------------------------------------------------------
# Front-matter y metadatos
# ----------------------------------------------------------------------
def partir_frontmatter(texto: str) -> tuple[dict, str]:
    if texto.lstrip().startswith("---"):
        texto = texto.lstrip()
        partes = texto.split("---", 2)
        if len(partes) >= 3 and yaml is not None:
            try:
                datos = yaml.safe_load(partes[1]) or {}
                if isinstance(datos, dict):
                    return datos, partes[2]
            except yaml.YAMLError:
                pass
    return {}, texto


def leer_yaml(ruta: Path) -> dict:
    if not ruta.exists() or yaml is None:
        return {}
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    return datos if isinstance(datos, dict) else {}


# ----------------------------------------------------------------------
# Índice / anclas de medición
# ----------------------------------------------------------------------
RE_HEADING = re.compile(
    r'<h([23])([^>]*?)>(.*?)</h\1>', re.DOTALL | re.IGNORECASE
)
RE_ID = re.compile(r'id="([^"]+)"')


RE_NUM_PROPIO = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+")


def preparar_headings(cuerpo_html: str, numero_cap: int) -> tuple[str, list[dict], bool]:
    """Garantiza un id en cada h2/h3, construye el índice y numera las
    secciones igual que los contadores CSS."""
    indice: list[dict] = []
    propios = 0
    n2 = 0
    seccion = 0
    subseccion = 0
    usados: set[str] = set()

    def reemplazo(m: re.Match) -> str:
        nonlocal seccion, subseccion, propios, n2
        nivel = int(m.group(1))
        atributos = m.group(2) or ""
        interior = m.group(3)
        texto = re.sub(r"<[^>]+>", "", interior).strip()

        mid = RE_ID.search(atributos)
        if mid:
            slug = mid.group(1)
        else:
            slug = slug_es(texto) or f"h{nivel}-{len(indice) + 1}"
            base, n = slug, 2
            while slug in usados:
                slug, n = f"{base}-{n}", n + 1
            atributos = f'{atributos} id="{slug}"'
        usados.add(slug)

        if nivel == 2:
            seccion += 1
            n2 += 1
            subseccion = 0
            numero = f"{numero_cap}.{seccion}"
        else:
            subseccion += 1
            numero = f"{numero_cap}.{seccion}.{subseccion}"

        # Si el autor ya numeró el título en el markdown, se respeta esa
        # numeración y se apagan los contadores CSS (evita "1.1 1.1 …").
        propio = RE_NUM_PROPIO.match(texto)
        if propio:
            if nivel == 2:
                propios += 1
            numero = propio.group(1)
            texto = texto[propio.end():]

        indice.append({"nivel": nivel, "numero": numero, "titulo": texto, "slug": slug})
        return f"<h{nivel}{atributos}>{interior}</h{nivel}>"

    html = RE_HEADING.sub(reemplazo, cuerpo_html)
    return html, indice, n2 > 0 and propios >= max(1, n2 // 2)


# ----------------------------------------------------------------------
# Render con Playwright (Python) — PDF + medición de páginas
#
# El libro y la presentación usan el mismo binding de Playwright, para que
# montar el proyecto en otra máquina sea un solo `pip install -r
# requisitos.txt` y no haga falta Node. Lo único que sigue siendo
# JavaScript es la función de medición, porque corre dentro del navegador.
# ----------------------------------------------------------------------
JS_MEDICION = r"""
(altoPx) => {
  const esSaltoForzado = (el) => {
    const s = getComputedStyle(el);
    const v = [s.breakBefore, s.pageBreakBefore].join(' ');
    return /page|always|left|right|recto|verso/.test(v);
  };
  const top = (el) => el.getBoundingClientRect().top + window.scrollY;

  const interes = Array.from(document.querySelectorAll(
    'h2[id], h3[id], section[id], main[id], header[id], .bc-portada, .bc-creditos, .bc-indice, .bc-apertura, .bc-ejercicios, .bc-clave'
  ));
  interes.sort((a, b) => top(a) - top(b));

  let extra = 0;
  const paginas = {};
  const orden = [];
  for (const el of interes) {
    const t = top(el);
    if (esSaltoForzado(el)) {
      const pos = t + extra;
      const borde = Math.ceil(pos / altoPx) * altoPx;
      if (borde - pos > 1) extra += borde - pos;
    }
    const num = Math.floor((t + extra) / altoPx) + 1;
    if (el.id) { paginas[el.id] = num; orden.push({ id: el.id, pagina: num }); }
  }
  return {
    paginas, orden,
    altoDocumento: document.documentElement.scrollHeight,
    paginasEstimadas: Math.max(1, Math.ceil((document.documentElement.scrollHeight + extra) / altoPx))
  };
}
"""


def plantilla_corrido(tokens: str, titulo_cap: str, titulo_libro: str, cual: str) -> str:
    """Encabezado/pie corridos para Chromium. Usa los tokens var(--bc-*)."""
    marco = (
        "<style>"
        + tokens
        + """
        html,body{margin:0;padding:0;width:100%;}
        .bc-corrido{
          box-sizing:border-box;
          width:100%;
          display:flex;align-items:center;justify-content:space-between;
          font-family:var(--bc-font-cuerpo);
          font-size:var(--bc-t-micro);
          letter-spacing:.1em;
          text-transform:uppercase;
          color:var(--bc-tinta-suave);
          padding:0 var(--bc-margen-ext) 0 var(--bc-margen-int);
        }
        .bc-corrido--encabezado{border-bottom:1px solid var(--bc-linea);padding-bottom:2px;}
        .bc-corrido--pie{border-top:1px solid var(--bc-linea);padding-top:2px;}
        .bc-corrido__capitulo{color:var(--bc-verde-700);}
        .bc-corrido__folio{
          font-family:var(--bc-font-titulo);font-size:var(--bc-t-pie);
          color:var(--bc-verde-900);letter-spacing:0;
        }
        </style>"""
    )
    if cual == "encabezado":
        cuerpo = (
            '<div class="bc-corrido bc-corrido--encabezado">'
            f'<span class="bc-corrido__capitulo">{titulo_cap}</span>'
            f"<span>{titulo_libro}</span></div>"
        )
    else:
        cuerpo = (
            '<div class="bc-corrido bc-corrido--pie">'
            f"<span>{titulo_libro}</span>"
            '<span class="bc-corrido__folio">'
            '<span class="pageNumber"></span> / <span class="totalPages"></span>'
            "</span></div>"
        )
    return marco + cuerpo


def _lanzar_chromium(p):
    """Chromium de Playwright; si no se descargó, el Chrome o Edge del
    sistema. Evita obligar a `playwright install` en la máquina del
    usuario cuando ya hay un navegador instalado."""
    intentos = [
        dict(),
        dict(channel="chrome"),
        dict(channel="msedge"),
        dict(executable_path="/usr/bin/google-chrome"),
    ]
    ultimo = None
    for kw in intentos:
        try:
            return p.chromium.launch(args=["--no-sandbox"], **kw)
        except Exception as exc:  # noqa: BLE001
            ultimo = exc
    raise RuntimeError(
        "no se pudo abrir Chromium para exportar el PDF. Instalá el navegador "
        "con `python -m playwright install chromium`, o tené Chrome/Edge en el "
        f"sistema. Último error: {ultimo}")


def exportar(html: Path, pdf: Path, tokens: str, titulo_cap: str, titulo_libro: str,
             ancho_px: float, alto_px: float) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "falta el paquete 'playwright' de Python: pip install -r requisitos.txt"
        ) from exc

    encabezado = plantilla_corrido(tokens, titulo_cap, titulo_libro, "encabezado")
    pie = plantilla_corrido(tokens, titulo_cap, titulo_libro, "pie")
    opciones = dict(format="A4", print_background=True, prefer_css_page_size=True)

    with tempfile.TemporaryDirectory() as tmp:
        pdf_limpio = Path(tmp) / "limpio.pdf"
        with sync_playwright() as p:
            navegador = _lanzar_chromium(p)
            try:
                pagina = navegador.new_page(viewport={
                    "width": int(round(ancho_px)), "height": int(round(alto_px))})
                pagina.emulate_media(media="print")
                pagina.goto(html.resolve().as_uri(), wait_until="load")
                pagina.evaluate("() => document.fonts && document.fonts.ready")

                medicion = pagina.evaluate(JS_MEDICION, alto_px)

                pagina.pdf(path=str(pdf.resolve()), display_header_footer=True,
                           header_template=encabezado, footer_template=pie, **opciones)
                # Segunda tirada sin encabezado ni pie: de ella se toma la
                # portada, que va a sangre completa.
                pagina.pdf(path=str(pdf_limpio), display_header_footer=False, **opciones)
            finally:
                navegador.close()
        fusionar_portada(pdf, pdf_limpio)
    return medicion


def fusionar_portada(pdf: Path, pdf_limpio: Path) -> None:
    """La portada va a sangre: se toma de la tirada sin encabezado/pie."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return
    if not pdf_limpio.exists():
        return
    con = PdfReader(str(pdf))
    sin = PdfReader(str(pdf_limpio))
    if len(con.pages) != len(sin.pages) or not con.pages:
        return
    escritor = PdfWriter()
    escritor.add_page(sin.pages[0])
    for pag in con.pages[1:]:
        escritor.add_page(pag)
    with open(pdf, "wb") as fh:
        escritor.write(fh)


def normalizar(texto: str) -> str:
    import unicodedata
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().lower()


def paginas_por_texto(pdf: Path, buscados: list[tuple[str, str]],
                      desde_marca: str | None = None,
                      ordenado: bool = False) -> dict:
    """Localiza en qué página del PDF aparece cada texto.

    Es el método exacto: lee el PDF ya paginado por Chromium en vez de
    estimar. `buscados` es una lista de (clave, texto a buscar).
    `desde_marca` permite saltear el índice, que repite los títulos.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return {}
    try:
        lector = PdfReader(str(pdf))
        textos = [normalizar(pag.extract_text() or "") for pag in lector.pages]
    except Exception:
        return {}

    inicio = 0
    if desde_marca:
        marca = normalizar(desde_marca)
        for i, t in enumerate(textos):
            if marca in t:
                inicio = i + 1
                break

    encontrados = {}
    cursor = inicio
    for clave, texto in buscados:
        aguja = normalizar(texto)
        if not aguja:
            continue
        for i in range(cursor if ordenado else inicio, len(textos)):
            if aguja in textos[i]:
                encontrados[clave] = i + 1
                if ordenado:
                    cursor = i
                break
    return encontrados


def paginas_del_pdf(pdf: Path) -> int | None:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf)).pages)
    except Exception:
        pass
    if shutil.which("pdfinfo"):
        salida = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        m = re.search(r"^Pages:\s+(\d+)", salida, re.MULTILINE)
        if m:
            return int(m.group(1))
    return None


# ----------------------------------------------------------------------
# Tokens → medidas de la caja de página
# ----------------------------------------------------------------------
def leer_token_mm(tokens: str, nombre: str, defecto: float) -> float:
    m = re.search(rf"--{nombre}\s*:\s*([\d.]+)mm", tokens)
    return float(m.group(1)) if m else defecto


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Construye el libro de texto (HTML A4 + PDF + mapa de páginas)."
    )
    ap.add_argument("--capitulo", required=True, help="identificador del capítulo, p. ej. cap01")
    ap.add_argument("--salida", default="salidas/libro", help="directorio de salida")
    ap.add_argument("--fuente", help="markdown alternativo (por defecto contenido/capitulos/<cap>/02-libro.md)")
    ap.add_argument("--ejercicios", help="markdown adicional con bloques :::ejercicio y :::clave")
    ap.add_argument("--sin-pdf", action="store_true", help="solo generar el HTML")
    ap.add_argument("--edicion", choices=("productor", "docente"), default="productor",
                    help="'docente' agrega la guia de clase y las respuestas explicadas")
    args = ap.parse_args(argv)

    cap = args.capitulo
    dir_cap = RAIZ / "contenido" / "capitulos" / cap
    fuente = Path(args.fuente).expanduser().resolve() if args.fuente else dir_cap / "02-libro.md"
    if not fuente.exists():
        print(f"error: no existe el markdown de origen: {fuente}", file=sys.stderr)
        return 2

    salida = Path(args.salida)
    if not salida.is_absolute():
        salida = RAIZ / salida
    salida.mkdir(parents=True, exist_ok=True)

    tokens = CSS_TOKENS.read_text(encoding="utf-8")
    css_libro = CSS_LIBRO.read_text(encoding="utf-8")

    # La edicion docente es el mismo libro del productor con una capa
    # encima: mismas paginas, misma maquetacion, para que el docente
    # estudie exactamente lo que el productor tiene delante.
    es_docente = args.edicion == "docente"
    if es_docente:
        css_docente = CSS_LIBRO.parent / "docente.css"
        if not css_docente.exists():
            print(f"error: falta {css_docente}", file=sys.stderr)
            return 2
        css_libro += "\n" + css_docente.read_text(encoding="utf-8")
        if args.salida == "salidas/libro":
            salida = RAIZ / "salidas" / "docente"
            salida.mkdir(parents=True, exist_ok=True)

    # --- metadatos -----------------------------------------------------
    meta = leer_yaml(dir_cap / "meta.yaml")
    texto = fuente.read_text(encoding="utf-8")
    fm, cuerpo_md = partir_frontmatter(texto)
    meta = {**meta, **fm}

    m = re.search(r"(\d+)", cap)
    numero_int = int(m.group(1)) if m else 1

    capitulo = {
        "id": cap,
        "numero": meta.get("numero", f"{numero_int:02d}"),
        "numero_int": numero_int,
        "titulo": meta.get("titulo", f"Capítulo {numero_int}"),
        "bajada": meta.get("bajada") or meta.get("subtitulo", ""),
        "docente": meta.get("docente") or meta.get("autor", ""),
        "duracion": meta.get("duracion", ""),
    }
    libro = {
        "coleccion": meta.get("coleccion", "Colección Biocontrol"),
        "titulo": meta.get("libro", "Biocontrol en el lote"),
        "subtitulo": meta.get("libro_subtitulo", "Manual práctico para productores agrícolas"),
        "edicion": meta.get("edicion", "Primera edición"),
        "anio": meta.get("anio", meta.get("año", 2026)),
        "editor": meta.get("editor", "Equipo Biocontrol"),
        "isbn": meta.get("isbn", ""),
        "licencia": meta.get("licencia", ""),
        "nota_legal": meta.get("nota_legal", ""),
        "muestra": bool(meta.get("muestra", "[MUESTRA]" in str(capitulo["titulo"]))),
        "edicion_docente": es_docente,
    }
    creditos = meta.get("creditos") or (
        [{"rol": "Material del docente", "nombre": capitulo["docente"]}]
        if capitulo["docente"] else []
    )

    # --- markdown → bloques → HTML -------------------------------------
    aparte: dict = {}
    nodos = parsear_bloques(cuerpo_md)
    cuerpo_html = render_nodos(nodos, fuente.parent, aparte)

    # Ejercicios: archivo indicado o, por defecto, 03-ejercicios.md del capítulo.
    ruta_ejercicios = (Path(args.ejercicios).expanduser().resolve()
                       if args.ejercicios else dir_cap / "03-ejercicios.md")
    if ruta_ejercicios != fuente:
        extra = ruta_ejercicios
        if extra.exists():
            _, cuerpo_extra = partir_frontmatter(extra.read_text(encoding="utf-8"))
            render_nodos(parsear_bloques(cuerpo_extra), extra.parent, aparte)

    # El título del capítulo ya lo compone la apertura: si el markdown
    # abre con un h1, se descarta para no repetirlo.
    cuerpo_html = re.sub(r"<h1[^>]*>.*?</h1>", "", cuerpo_html, count=1, flags=re.DOTALL)

    # --- guia del docente ----------------------------------------------
    if es_docente:
        ruta_docente = dir_cap / "04-docente.md"
        if ruta_docente.exists():
            _, cuerpo_doc = partir_frontmatter(ruta_docente.read_text(encoding="utf-8"))
            # El h1 propio del archivo se reemplaza por el rotulo de la seccion.
            cuerpo_doc = re.sub(r"(?m)^#\s+.*$", "", cuerpo_doc, count=1)
            html_doc = render_nodos(parsear_bloques(cuerpo_doc), ruta_docente.parent, {})
            cuerpo_html += (
                '<section class="bc-docente">'
                '<p class="bc-docente__rotulo">Solo para el docente</p>'
                '<h1>Guia de clase y respuestas explicadas</h1>'
                + html_doc + '</section>'
            )
        else:
            print(f"  aviso: no existe {ruta_docente}; la edicion docente "
                  "sale sin guia de clase", file=sys.stderr)

    cuerpo_html, indice, numeracion_propia = preparar_headings(cuerpo_html, numero_int)

    resumen = aparte.get("resumen") or meta.get("resumen") or []
    ejercicios = aparte.get("ejercicios", [])
    clave = aparte.get("clave", [])

    # --- Jinja2 --------------------------------------------------------
    env = Environment(
        loader=FileSystemLoader(str(DIR_PLANTILLAS)),
        autoescape=True,
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    plantilla = env.get_template("capitulo.html")

    def render(indice_render):
        return plantilla.render(
            css_tokens=Markup(tokens),
            css_libro=Markup(css_libro),
            libro=libro,
            capitulo=capitulo,
            creditos=creditos,
            indice=indice_render,
            cuerpo_html=Markup(cuerpo_html),
            resumen=[Markup(r) for r in resumen],
            ejercicios=ejercicios,
            clave=clave,
            instruccion=meta.get("instruccion_ejercicios"),
            numeracion_propia=numeracion_propia,
        )

    archivo_html = salida / f"{cap}.html"
    archivo_html.write_text(render(indice), encoding="utf-8")
    print(f"HTML  → {archivo_html}")

    if args.sin_pdf:
        return 0

    # --- medidas de la caja de página ----------------------------------
    ancho_mm = (leer_token_mm(tokens, "bc-pagina-ancho", 210.0)
                - leer_token_mm(tokens, "bc-margen-int", 22.0)
                - leer_token_mm(tokens, "bc-margen-ext", 16.0))
    alto_mm = (leer_token_mm(tokens, "bc-pagina-alto", 297.0)
               - leer_token_mm(tokens, "bc-margen-sup", 18.0)
               - leer_token_mm(tokens, "bc-margen-inf", 18.0))

    archivo_pdf = salida / f"{cap}.pdf"
    titulo_cap = f"{capitulo['numero']} · {capitulo['titulo']}"
    medicion = exportar(archivo_html, archivo_pdf, tokens, titulo_cap,
                        libro["titulo"], ancho_mm * MM_A_PX, alto_mm * MM_A_PX)

    def resolver_paginas(medicion_actual: dict) -> dict:
        """Mezcla la medición del navegador (estimación) con la lectura
        del PDF ya paginado (exacta, tiene prioridad)."""
        paginas = dict(medicion_actual.get("paginas", {}))
        secciones = [(it["slug"], it["titulo"]) for it in indice]
        buscados = [
            ("creditos", "Créditos de la edición"),
            ("apertura", capitulo["titulo"]),
            ("resumen", "Resumen del capítulo"),
            ("ejercicios", f"Ejercicios del capítulo {capitulo['numero']}"),
            ("clave", "Clave de respuestas"),
            ("clave-respuestas", "Clave de respuestas"),
            ("ejercicios-titulo", f"Ejercicios del capítulo {capitulo['numero']}"),
        ]
        exactas = paginas_por_texto(archivo_pdf, buscados,
                                    desde_marca="Índice del capítulo")
        exactas.update(paginas_por_texto(archivo_pdf, secciones,
                                         desde_marca="Índice del capítulo",
                                         ordenado=True))
        exactas.update(paginas_por_texto(archivo_pdf, [("indice", "Índice del capítulo")]))
        paginas.update({k: v for k, v in exactas.items() if v})
        paginas["portada"] = 1
        if "apertura" in paginas:
            paginas["cuerpo"] = paginas["apertura"]
        return paginas

    # --- segunda pasada: el índice ya lleva las páginas reales ---------
    paginas = resolver_paginas(medicion)
    for it in indice:
        it["pagina"] = paginas.get(it["slug"], "—")
    archivo_html.write_text(render(indice), encoding="utf-8")
    medicion = exportar(archivo_html, archivo_pdf, tokens, titulo_cap,
                        libro["titulo"], ancho_mm * MM_A_PX, alto_mm * MM_A_PX)
    paginas = resolver_paginas(medicion)
    for it in indice:
        it["pagina"] = paginas.get(it["slug"], "—")

    total = paginas_del_pdf(archivo_pdf)
    print(f"PDF   → {archivo_pdf} ({total if total else '?'} páginas)")

    # --- mapa de páginas para verificar-sync.py ------------------------
    mapa = {
        "capitulo": cap,
        "titulo": capitulo["titulo"],
        "pdf": str(archivo_pdf.relative_to(RAIZ)) if archivo_pdf.is_relative_to(RAIZ) else str(archivo_pdf),
        "total_paginas": total or medicion.get("paginasEstimadas"),
        "alto_pagina_px": alto_mm * MM_A_PX,
        "paginas": {
            **{it["slug"]: paginas.get(it["slug"]) for it in indice},
            **{k: v for k, v in paginas.items()},
        },
        "secciones": [
            {"nivel": it["nivel"], "numero": it["numero"], "titulo": it["titulo"],
             "slug": it["slug"], "pagina": paginas.get(it["slug"])}
            for it in indice
        ],
    }
    archivo_json = salida / f"{cap}-paginas.json"
    archivo_json.write_text(json.dumps(mapa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"MAPA  → {archivo_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
