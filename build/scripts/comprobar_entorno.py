#!/usr/bin/env python3
"""
Comprueba que la maquina puede construir los entregables, ANTES de que
falle un build a las once de la noche.

    python3 build/scripts/comprobar_entorno.py
"""
import importlib, shutil, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

PAQUETES = [
    ("jinja2",     "plantillas",                      "pip install -r requisitos.txt"),
    ("markdown",   "markdown -> HTML",                "pip install -r requisitos.txt"),
    ("playwright", "render a PDF y PNG",              "pip install -r requisitos.txt"),
    ("pypdf",      "medir y fusionar PDFs",           "pip install -r requisitos.txt"),
    ("pptx",       "leer y escribir PowerPoint",      "pip install python-pptx"),
    ("docx",       "leer Word",                       "pip install python-docx"),
    ("yaml",       "meta.yaml y front-matter",        "pip install PyYAML"),
    ("PIL",        "imagenes",                        "pip install Pillow"),
]

def main() -> int:
    fallos = []
    print("Paquetes de Python")
    for modulo, para_que, arreglo in PAQUETES:
        try:
            importlib.import_module(modulo)
            print(f"  ok      {modulo:<12} {para_que}")
        except ImportError:
            print(f"  FALTA   {modulo:<12} {para_que}   ->  {arreglo}")
            fallos.append(modulo)

    print("\nNavegador (para exportar PDF y PNG)")
    navegador = None
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            for kw, nombre in ((dict(), "Chromium de Playwright"),
                               (dict(channel="chrome"), "Chrome del sistema"),
                               (dict(channel="msedge"), "Edge del sistema")):
                try:
                    b = p.chromium.launch(args=["--no-sandbox"], **kw)
                    b.close()
                    navegador = nombre
                    break
                except Exception:
                    continue
    except ImportError:
        pass
    if navegador:
        print(f"  ok      {navegador}")
    else:
        print("  FALTA   ningun Chromium disponible")
        print("          ->  python -m playwright install chromium")
        fallos.append("chromium")

    print("\nOpcional")
    print(f"  {'ok     ' if shutil.which('pdfinfo') else 'ausente'} pdfinfo "
          "(solo para informar el numero de paginas)")

    print("\nArchivos del proyecto")
    for rel in ("diseno/css/tokens.css", "diseno/css/libro.css",
                "diseno/css/presentacion.css", "contenido/ESQUEMA.md"):
        existe = (RAIZ / rel).exists()
        print(f"  {'ok     ' if existe else 'FALTA  '} {rel}")
        if not existe:
            fallos.append(rel)

    if fallos:
        print(f"\nFaltan {len(fallos)} cosas: " + ", ".join(fallos))
        return 1
    print("\nTodo listo: se pueden construir libro, presentacion y edicion docente.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
