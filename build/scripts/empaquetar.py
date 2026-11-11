#!/usr/bin/env python3
"""
Arma un .zip por capitulo con TODO lo entregable y lo que lo produjo.

    python3 build/scripts/empaquetar.py --capitulo cap01
    python3 build/scripts/empaquetar.py --todos

Cada zip lleva:
    LEEME.txt                      que es cada cosa
    libro/        PDF + HTML + mapa de paginas
    docente/      PDF + HTML + mapa de paginas
    presentacion/ PPTX + PDF + HTML + PNG por diapositiva
    fuente/       los markdown del capitulo (editables)
    imagenes/     las figuras e imagenes del capitulo

Antes de empaquetar comprueba que el PDF exista, tenga paginas y que su
PRIMERA PAGINA sea la portada: un zip con el libro sin portada parece
completo y no lo esta.
"""
import argparse, shutil, sys, zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def paginas(pdf: Path):
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf)).pages)
    except Exception:
        return None


def portada_ok(pdf: Path, titulo: str):
    """La portada es la pagina 1 y no lleva encabezado corrido. Se valida
    que exista texto del titulo y que NO aparezca el folio corrido."""
    try:
        from pypdf import PdfReader
        p1 = (PdfReader(str(pdf)).pages[0].extract_text() or "")
    except Exception as e:
        return False, f"no se pudo leer la primera pagina ({e})"
    clave = (titulo or "").split("—")[0].strip()[:18]
    if clave and clave.lower() not in p1.lower():
        return False, f"la pagina 1 no parece la portada: no dice «{clave}»"
    if "BIOCONTROL EN EL LOTE" in p1.upper() and len(p1) > 400:
        return False, "la pagina 1 trae encabezado corrido: la portada no salio a sangre"
    return True, "portada correcta"


def leer_titulo(cap: str):
    f = RAIZ / "contenido" / "capitulos" / cap / "meta.yaml"
    if not f.exists():
        return cap
    for linea in f.read_text(encoding="utf-8").splitlines():
        if linea.strip().startswith("titulo:"):
            return linea.split(":", 1)[1].strip().strip('"\'')
    return cap


def empaquetar(cap: str, destino_dir: Path) -> Path | None:
    titulo = leer_titulo(cap)
    piezas = []          # (ruta_origen, ruta_dentro_del_zip)
    avisos = []

    libro = RAIZ / "salidas" / "libro" / f"{cap}.pdf"
    docente = RAIZ / "salidas" / "docente" / f"{cap}.pdf"
    pres_pptx = RAIZ / "salidas" / "presentacion" / f"{cap}.pptx"

    if not libro.exists():
        print(f"  {cap}: FALTA el libro ({libro}). Construilo primero.", file=sys.stderr)
        return None

    # --- comprobaciones antes de empaquetar ---
    n = paginas(libro)
    if not n:
        print(f"  {cap}: el PDF del libro no tiene paginas legibles.", file=sys.stderr)
        return None
    ok, motivo = portada_ok(libro, titulo)
    if not ok:
        avisos.append(f"LIBRO: {motivo}")
    if docente.exists():
        ok_d, motivo_d = portada_ok(docente, titulo)
        if not ok_d:
            avisos.append(f"EDICION DOCENTE: {motivo_d}")
    if not pres_pptx.exists():
        avisos.append("no hay .pptx de la presentacion")

    # --- piezas ---
    for sub, carpeta in (("libro", "libro"), ("docente", "docente")):
        d = RAIZ / "salidas" / sub
        for ext in ("pdf", "html", "-paginas.json"):
            f = d / (f"{cap}{ext}" if ext.startswith("-") else f"{cap}.{ext}")
            if f.exists():
                piezas.append((f, f"{carpeta}/{f.name}"))

    dp = RAIZ / "salidas" / "presentacion"
    for ext in ("pptx", "pdf", "html"):
        f = dp / f"{cap}.{ext}"
        if f.exists():
            piezas.append((f, f"presentacion/{f.name}"))
    png = dp / f"_png-{cap}"
    if png.is_dir():
        for f in sorted(png.glob("*.png")):
            piezas.append((f, f"presentacion/diapositivas-png/{f.name}"))

    for f in sorted((RAIZ / "contenido" / "capitulos" / cap).glob("*")):
        if f.is_file():
            piezas.append((f, f"fuente/{f.name}"))

    img = RAIZ / "diseno" / "assets" / cap
    if img.is_dir():
        for f in sorted(img.iterdir()):
            if f.is_file():
                piezas.append((f, f"imagenes/{f.name}"))

    # --- LEEME ---
    leeme = [
        f"{titulo}",
        "=" * len(titulo), "",
        f"Libro del productor .......... libro/{cap}.pdf  ({n} paginas)",
    ]
    nd = paginas(docente) if docente.exists() else None
    leeme.append(f"Edicion docente .............. docente/{cap}.pdf"
                 + (f"  ({nd} paginas)" if nd else "   (no generada)"))
    leeme += [
        f"Presentacion (PowerPoint) .... presentacion/{cap}.pptx",
        f"Presentacion (PDF) ........... presentacion/{cap}.pdf",
        "",
        "Que es cada carpeta",
        "-------------------",
        "libro/         Lo que recibe el productor. El HTML es el mismo",
        "               documento por si hay que reimprimirlo desde el navegador.",
        "docente/       El mismo libro mas el guion de clase y las respuestas.",
        "presentacion/  El .pptx se edita en PowerPoint. Las notas del expositor",
        "               estan en el panel de notas de cada diapositiva.",
        "               diapositivas-png/ son las mismas en imagen suelta.",
        "fuente/        Los textos en markdown. Es lo que hay que editar para",
        "               cambiar el contenido; los PDF se regeneran despues.",
        "imagenes/      Figuras e imagenes del capitulo.",
        "",
        "Para regenerar los PDF despues de editar la fuente:",
        f"  python build/scripts/construir_libro.py --capitulo {cap}",
        f"  python build/scripts/realinear_paginas.py --capitulo {cap}",
        f"  python build/scripts/construir_libro.py --capitulo {cap}",
        "",
    ]
    if avisos:
        leeme += ["AVISOS", "------"] + [f"  - {a}" for a in avisos] + [""]

    destino_dir.mkdir(parents=True, exist_ok=True)
    zip_path = destino_dir / f"{cap}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LEEME.txt", "\n".join(leeme))
        for origen, dentro in piezas:
            z.write(origen, dentro)

    mb = zip_path.stat().st_size / 1024 / 1024
    print(f"  {cap}: {zip_path.name}  ({len(piezas)+1} archivos, {mb:.1f} MB)"
          + ("  [con avisos]" if avisos else ""))
    for a in avisos:
        print(f"      aviso: {a}")
    return zip_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capitulo")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--salida", default="salidas/entregas")
    a = ap.parse_args()

    destino = Path(a.salida)
    if not destino.is_absolute():
        destino = RAIZ / destino

    if a.todos:
        caps = sorted(d.name for d in (RAIZ / "contenido" / "capitulos").iterdir()
                      if d.is_dir() and (RAIZ / "salidas" / "libro" / f"{d.name}.pdf").exists())
    elif a.capitulo:
        caps = [a.capitulo]
    else:
        print("error: indica --capitulo capNN o --todos", file=sys.stderr)
        return 2

    if not caps:
        print("No hay capitulos construidos que empaquetar.", file=sys.stderr)
        return 2

    print(f"Empaquetando {len(caps)} capitulo(s) en {destino}")
    hechos = [z for c in caps if (z := empaquetar(c, destino))]
    print(f"\n{len(hechos)} de {len(caps)} empaquetados.")
    return 0 if len(hechos) == len(caps) else 1


if __name__ == "__main__":
    sys.exit(main())
