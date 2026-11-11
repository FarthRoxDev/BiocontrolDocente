#!/usr/bin/env python3
"""
Ingestor de material docente: PPTX / DOCX / PDF  ->  Markdown crudo + imagenes.

Uso:
    python3 build/scripts/ingerir_fuentes.py contenido/fuentes/*.pptx --capitulo cap01

Produce:
  - contenido/capitulos/capNN/01-fuente.md  transcripcion FIEL del material
    (un encabezado por diapositiva o seccion, el texto tal cual, y marcadores
    explicitos para lo que no se pudo extraer).
  - diseno/assets/capNN/*                   las imagenes incrustadas, ya con
    la ruta relativa lista para pegar como :::figura en 02-libro.md.

NO interpreta ni reescribe: eso lo hace despues la skill `redactar-capitulo`.
"""
import argparse, os, sys, datetime, hashlib, re, unicodedata, glob as globlib
from pathlib import Path

# Formatos que el motor del libro puede incrustar directamente en el PDF.
EXT_RENDERIZABLES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
# Por debajo de esto casi siempre son logos, vinetas o lineas decorativas.
BYTES_DECORATIVA = 8 * 1024


def slug(texto):
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "archivo"


class Imagenes:
    """Guarda las imagenes incrustadas en diseno/assets/capNN/ y devuelve la
    ruta relativa DESDE contenido/capitulos/capNN/, que es la que entiende
    el bloque :::figura de construir_libro.py."""

    def __init__(self, raiz, capitulo):
        self.dir = Path(raiz) / "diseno" / "assets" / capitulo
        self.rel = f"../../../diseno/assets/{capitulo}"
        self.vistas = {}          # hash -> nombre ya guardado (evita repetir logos)
        self.guardadas = 0
        self.repetidas = 0
        self.no_renderizables = []

    def guardar(self, datos, ext, base):
        ext = (ext or "").lower()
        if not ext.startswith("."):
            ext = "." + ext if ext else ".bin"
        firma = hashlib.sha1(datos).hexdigest()
        if firma in self.vistas:
            self.repetidas += 1
            return self.vistas[firma], True, len(datos)

        self.dir.mkdir(parents=True, exist_ok=True)
        nombre = f"{base}{ext}"
        destino = self.dir / nombre
        n = 2
        while destino.exists():
            nombre = f"{base}-{n}{ext}"
            destino = self.dir / nombre
            n += 1
        destino.write_bytes(datos)
        self.guardadas += 1
        if ext not in EXT_RENDERIZABLES:
            self.no_renderizables.append(nombre)
        self.vistas[firma] = nombre
        return nombre, False, len(datos)

    def referencia(self, nombre, tam, repetida, nota=""):
        """Linea markdown lista para copiar a 02-libro.md como :::figura."""
        marcas = []
        if repetida:
            marcas.append("repetida en el material (logo o plantilla?)")
        if tam < BYTES_DECORATIVA:
            marcas.append("muy pequena, probablemente decorativa")
        if Path(nombre).suffix.lower() not in EXT_RENDERIZABLES:
            marcas.append(f"formato {Path(nombre).suffix} no se incrusta en el PDF; reexportar a PNG")
        if nota:
            marcas.append(nota)
        aviso = f"  <!-- {'; '.join(marcas)} -->" if marcas else ""
        return f"![]({self.rel}/{nombre}){aviso}"


def de_pptx(ruta, img, base):
    from pptx import Presentation
    pres, salida = Presentation(ruta), []
    for i, slide in enumerate(pres.slides, 1):
        salida.append(f"\n## Diapositiva {i}\n")
        textos, figuras = [], []

        def recorrer(formas, n=0):
            """Las imagenes pueden venir dentro de grupos, hay que bajar."""
            for sh in formas:
                if sh.shape_type == 6 and hasattr(sh, "shapes"):   # grupo
                    recorrer(sh.shapes, n)
                    continue
                if getattr(sh, "image", None) is not None:
                    try:
                        blob = sh.image.blob
                        ext = "." + (sh.image.ext or "bin")
                    except Exception as e:                          # imagen rota o enlazada
                        figuras.append(f"<!-- FUENTE: imagen no extraible en diapositiva {i}: {e} -->")
                        continue
                    nombre, repetida, tam = img.guardar(
                        blob, ext, f"{base}-d{i:02d}-{len(figuras) + 1}")
                    pie = ""
                    if getattr(sh, "name", "") and not sh.name.lower().startswith(("picture", "imagen", "image")):
                        pie = f"nombre en el PPTX: {sh.name}"
                    figuras.append(img.referencia(nombre, tam, repetida, pie))
                    continue
                if getattr(sh, "has_table", False) and sh.has_table:
                    textos.append("\n".join(
                        " | ".join(c.text.strip() for c in f.cells) for f in sh.table.rows))
                    continue
                if getattr(sh, "has_chart", False) and sh.has_chart:
                    figuras.append(f"<!-- FUENTE: grafico nativo de PowerPoint en la diapositiva {i}. "
                                   "No se puede extraer como imagen: rehacerlo o pedir captura al docente. -->")
                    continue
                if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
                    t = sh.text_frame.text.strip()
                    if t:
                        textos.append(t)

        recorrer(slide.shapes)
        salida.append("\n\n".join(textos) if textos else "_(sin texto extraible)_")
        if figuras:
            salida.append("\n\n" + "\n\n".join(figuras))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            notas = slide.notes_slide.notes_text_frame.text.strip()
            salida.append(f"\n\n> **Notas del docente:** {notas}")
    return "\n".join(salida)


def de_docx(ruta, img, base):
    import docx
    doc, salida = docx.Document(ruta), []
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        est = (p.style.name or "").lower()
        if "heading 1" in est:   salida.append(f"\n## {t}\n")
        elif "heading 2" in est: salida.append(f"\n### {t}\n")
        elif "heading 3" in est: salida.append(f"\n#### {t}\n")
        elif "list" in est:      salida.append(f"- {t}")
        else:                    salida.append(t)
    for tb in doc.tables:
        salida.append("")
        for fila in tb.rows:
            salida.append(" | ".join(c.text.strip() for c in fila.cells))

    # Las imagenes de un .docx no tienen posicion fiable en el texto: se
    # listan juntas al final y el redactor decide donde van.
    refs = []
    for nombre_parte, parte in doc.part.related_parts.items():
        tipo = getattr(parte, "content_type", "") or ""
        if not tipo.startswith("image/"):
            continue
        ext = "." + tipo.split("/")[-1].split("+")[0]
        n, repetida, tam = img.guardar(parte.blob, ext, f"{base}-img-{len(refs) + 1}")
        refs.append(img.referencia(n, tam, repetida))
    if refs:
        salida.append("\n### Imagenes del documento\n")
        salida.append("<!-- FUENTE: un .docx no conserva la posicion de las imagenes "
                      "en el texto; ubicarlas al redactar 02-libro.md. -->\n")
        salida.append("\n\n".join(refs))
    return "\n\n".join(salida)


def de_pdf(ruta, img, base):
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    r, salida = PdfReader(ruta), []
    for i, pg in enumerate(r.pages, 1):
        txt = (pg.extract_text() or "").strip()
        salida.append(f"\n## Pagina {i}\n")
        salida.append(txt if txt else
                      "<!-- FUENTE: pagina sin texto extraible (probablemente escaneada). "
                      "Requiere OCR o transcripcion manual. -->")
        refs = []
        try:
            for n_img, imagen in enumerate(pg.images, 1):
                datos = imagen.data
                ext = os.path.splitext(imagen.name)[1] or ".png"
                nombre, repetida, tam = img.guardar(datos, ext, f"{base}-p{i:02d}-{n_img}")
                refs.append(img.referencia(nombre, tam, repetida))
        except Exception as e:
            refs.append(f"<!-- FUENTE: no se pudieron extraer las imagenes de la pagina {i}: {e} -->")
        if refs:
            salida.append("\n" + "\n\n".join(refs))
    return "\n".join(salida)


LECTORES = {".pptx": de_pptx, ".docx": de_docx, ".pdf": de_pdf}

def main():
    ap = argparse.ArgumentParser(
        description="Convierte el material del docente en 01-fuente.md y extrae sus imagenes.")
    ap.add_argument("archivos", nargs="+",
                    help="archivos, comodines (*.pptx) o una carpeta con el material")
    ap.add_argument("--capitulo", required=True, help="p.ej. cap01")
    ap.add_argument("--docente", default="<completar>")
    ap.add_argument("--raiz", default=str(Path(__file__).resolve().parents[2]),
                    help="raiz del repositorio (por defecto, la del propio script)")
    ap.add_argument("--sin-imagenes", action="store_true",
                    help="no extraer las imagenes incrustadas")
    a = ap.parse_args()

    # PowerShell y cmd NO expanden los comodines: le pasan "*.pptx" literal
    # al programa. Y apuntar a la carpeta entera es lo mas comodo cuando el
    # material del docente esta todo junto. Se resuelven los dos casos aqui.
    archivos = []
    for patron in a.archivos:
        ruta = Path(patron)
        if ruta.is_dir():
            for ext in sorted(LECTORES):
                archivos += sorted(str(f) for f in ruta.glob(f"*{ext}"))
        elif any(c in patron for c in "*?[") and not ruta.exists():
            encontrados = sorted(globlib.glob(patron))
            if not encontrados:
                print(f"  nada coincide con: {patron}", file=sys.stderr)
            archivos += encontrados
        else:
            archivos.append(patron)
    if not archivos:
        print("error: no se encontro ningun archivo que leer", file=sys.stderr)
        return 2
    a.archivos = archivos

    raiz = Path(a.raiz).resolve()
    img = Imagenes(raiz, a.capitulo)

    partes = [
        f"# Fuente — {a.capitulo}", "",
        f"- **Docente:** {a.docente}",
        f"- **Ingerido:** {datetime.date.today().isoformat()}",
        "- **Archivos:** " + ", ".join(os.path.basename(f) for f in a.archivos), "",
        "> Transcripcion fiel del material entregado. No editar para estilo: "
        "la redaccion didactica se hace en `02-libro.md`.",
        ">",
        "> Las imagenes se guardaron en `diseno/assets/" + a.capitulo + "/` y aparecen "
        "abajo con su ruta ya lista para pegar en un bloque `:::figura`.", "",
    ]

    leidos = 0
    for f in a.archivos:
        ruta = Path(f)
        lector = LECTORES.get(ruta.suffix.lower())
        if not lector:
            print(f"  omitido (formato no soportado): {f}", file=sys.stderr); continue
        if not ruta.exists():
            print(f"  no existe: {f}", file=sys.stderr); continue
        print(f"  leyendo {f}")
        destino_img = img if not a.sin_imagenes else Imagenes(raiz, a.capitulo + "/__descartado")
        partes += [f"\n---\n\n# Archivo: {ruta.name}\n",
                   lector(str(ruta), destino_img, slug(ruta.stem))]
        leidos += 1

    if not leidos:
        print("error: no se pudo leer ningun archivo", file=sys.stderr)
        return 2

    destino = raiz / "contenido" / "capitulos" / a.capitulo / "01-fuente.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(partes) + "\n", encoding="utf-8")

    print(f"\nEscrito: {destino}")
    if not a.sin_imagenes:
        print(f"Imagenes: {img.guardadas} guardadas en {img.dir}"
              + (f", {img.repetidas} repetidas (reutilizan archivo)" if img.repetidas else ""))
        if img.no_renderizables:
            print("  aviso: estos formatos no se incrustan en el PDF, reexportarlos a PNG: "
                  + ", ".join(img.no_renderizables), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
