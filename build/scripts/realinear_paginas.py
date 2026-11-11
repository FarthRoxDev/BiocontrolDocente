#!/usr/bin/env python3
"""
Realinea las marcas <!-- pagina: N --> de 02-libro.md y los `pagina:` de
05-diapositivas.md con la paginacion REAL que midio el build.

Cada vez que el capitulo cambia de largo —se agrega una figura, crece un
parrafo— las secciones se corren de pagina y esas referencias quedan
mintiendo. Una marca corrida es el expositor diciendo "abranlo en la 12" y
la gente cayendo en la 11.

    python3 build/scripts/construir_libro.py --capitulo cap01   # mide
    python3 build/scripts/realinear_paginas.py --capitulo cap01 # corrige
    python3 build/scripts/construir_libro.py --capitulo cap01   # reimprime

Con --verificar no escribe nada: solo informa y devuelve 1 si hay desfase.
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def normalizar(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capitulo", required=True)
    ap.add_argument("--verificar", action="store_true",
                    help="no escribe: solo informa el desfase")
    a = ap.parse_args()

    dir_cap = RAIZ / "contenido" / "capitulos" / a.capitulo
    mapa = RAIZ / "salidas" / "libro" / f"{a.capitulo}-paginas.json"
    if not mapa.exists():
        print(f"error: falta {mapa}. Construi el libro primero:\n"
              f"  python3 build/scripts/construir_libro.py --capitulo {a.capitulo}",
              file=sys.stderr)
        return 2

    secciones = json.loads(mapa.read_text(encoding="utf-8"))["secciones"]
    por_titulo = {normalizar(s["titulo"]): s["pagina"] for s in secciones}
    por_slug = {s["slug"]: s["pagina"] for s in secciones}

    desfases = 0

    # ---- 02-libro.md: marca <!-- pagina: N --> seguida de un encabezado ----
    libro = dir_cap / "02-libro.md"
    if libro.exists():
        texto = libro.read_text(encoding="utf-8")
        lineas = texto.split("\n")
        for i, linea in enumerate(lineas):
            m = re.match(r"^<!-- pagina: (\d+) -->$", linea.strip())
            if not m:
                continue
            # buscar el proximo encabazado para saber de que seccion habla
            titulo = None
            for j in range(i + 1, min(i + 8, len(lineas))):
                h = re.match(r"^#{1,4}\s+(.+?)\s*$", lineas[j])
                if h:
                    titulo = normalizar(h.group(1))
                    break
            if titulo is None or titulo not in por_titulo:
                continue
            real = por_titulo[titulo]
            if int(m.group(1)) != real:
                desfases += 1
                print(f"  02-libro.md linea {i+1}: {m.group(1)} -> {real}")
                lineas[i] = f"<!-- pagina: {real} -->"
        if not a.verificar:
            libro.write_text("\n".join(lineas), encoding="utf-8")

    # ---- 05-diapositivas.md: `pagina:` guiado por `seccion:` ----
    mazo = dir_cap / "05-diapositivas.md"
    if mazo.exists():
        texto = mazo.read_text(encoding="utf-8")
        bloques = texto.split("\n---\n")
        cambiado = False
        for k, bloque in enumerate(bloques):
            ms = re.search(r"(?m)^seccion:\s*[\"']?([\w-]+)[\"']?\s*$", bloque)
            mp = re.search(r"(?m)^pagina:\s*(\d+)\s*$", bloque)
            if not (ms and mp):
                continue
            real = por_slug.get(ms.group(1))
            if real is None or int(mp.group(1)) == real:
                continue
            desfases += 1
            print(f"  05-diapositivas.md seccion '{ms.group(1)}': "
                  f"{mp.group(1)} -> {real}")
            bloques[k] = re.sub(r"(?m)^pagina:\s*\d+\s*$", f"pagina: {real}", bloque)
            cambiado = True
        if cambiado and not a.verificar:
            mazo.write_text("\n---\n".join(bloques), encoding="utf-8")

    if desfases == 0:
        print("Sin desfases: las referencias coinciden con la paginacion real.")
        return 0
    if a.verificar:
        print(f"\n{desfases} referencia(s) desfasada(s). Corregilas con:\n"
              f"  python3 build/scripts/realinear_paginas.py --capitulo {a.capitulo}")
        return 1
    print(f"\n{desfases} referencia(s) corregida(s). Volve a construir el libro "
          "para que el indice y los folios salgan con los numeros nuevos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
