#!/usr/bin/env python3
"""
Ingestor de material docente: PPTX / DOCX / PDF  ->  Markdown crudo.

Uso:
    python3 build/scripts/ingerir_fuentes.py contenido/fuentes/*.pptx --capitulo cap01

Produce contenido/capitulos/capNN/01-fuente.md con la transcripcion FIEL del
material del docente: un encabezado por diapositiva o seccion, el texto tal
cual, y marcadores explicitos para lo que no se pudo extraer (imagenes,
graficos, texto en imagen). NO interpreta ni reescribe: eso lo hace despues
la skill `redactar-capitulo`.
"""
import argparse, os, sys, datetime

def de_pptx(ruta):
    from pptx import Presentation
    pres, salida = Presentation(ruta), []
    for i, slide in enumerate(pres.slides, 1):
        salida.append(f"\n## Diapositiva {i}\n")
        textos, imagenes, tablas = [], 0, 0
        for sh in slide.shapes:
            if sh.shape_type == 13 or sh.__class__.__name__ == "Picture":
                imagenes += 1
            if getattr(sh, "has_table", False) and sh.has_table:
                tablas += 1
                filas = [" | ".join(c.text.strip() for c in f.cells) for f in sh.table.rows]
                textos.append("\n".join(filas))
                continue
            if sh.has_text_frame:
                t = sh.text_frame.text.strip()
                if t:
                    textos.append(t)
        salida.append("\n\n".join(textos) if textos else "_(sin texto extraible)_")
        if imagenes:
            salida.append(f"\n\n<!-- FUENTE: {imagenes} imagen(es) en esta diapositiva, "
                          f"no extraidas. Describir o reexportar a diseno/assets/ -->")
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            notas = slide.notes_slide.notes_text_frame.text.strip()
            salida.append(f"\n\n> **Notas del docente:** {notas}")
    return "\n".join(salida)

def de_docx(ruta):
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
    return "\n\n".join(salida)

def de_pdf(ruta):
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
    return "\n".join(salida)

LECTORES = {".pptx": de_pptx, ".docx": de_docx, ".pdf": de_pdf}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archivos", nargs="+")
    ap.add_argument("--capitulo", required=True, help="p.ej. cap01")
    ap.add_argument("--docente", default="<completar>")
    a = ap.parse_args()

    partes = [
        f"# Fuente — {a.capitulo}", "",
        f"- **Docente:** {a.docente}",
        f"- **Ingerido:** {datetime.date.today().isoformat()}",
        f"- **Archivos:** " + ", ".join(os.path.basename(f) for f in a.archivos), "",
        "> Transcripcion fiel del material entregado. No editar para estilo: "
        "la redaccion didactica se hace en `02-libro.md`.", "",
    ]
    for f in a.archivos:
        ext = os.path.splitext(f)[1].lower()
        lector = LECTORES.get(ext)
        if not lector:
            print(f"  omitido (formato no soportado): {f}", file=sys.stderr); continue
        if not os.path.exists(f):
            print(f"  no existe: {f}", file=sys.stderr); continue
        print(f"  leyendo {f}")
        partes += [f"\n---\n\n# Archivo: {os.path.basename(f)}\n", lector(f)]

    destino = os.path.join("contenido", "capitulos", a.capitulo, "01-fuente.md")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write("\n".join(partes) + "\n")
    print(f"\nEscrito: {destino}")

if __name__ == "__main__":
    main()
