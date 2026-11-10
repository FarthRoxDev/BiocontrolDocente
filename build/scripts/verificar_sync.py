#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_sync.py — BIOCONTROL
Compara el `pagina:` declarado en cada diapositiva contra la paginacion real
que produjo el libro (`salidas/libro/capNN-paginas.json`, lo genera el
constructor del libro).

Uso:
    python3 build/scripts/verificar_sync.py --capitulo cap01
    python3 build/scripts/verificar_sync.py --capitulo cap01 --paginas otra/ruta.json
    python3 build/scripts/verificar_sync.py --diapositivas mazo.md --paginas pags.json

Codigos de salida:
    0  todas las diapositivas sincronizadas
    1  hay DESFASE (o alguna diapositiva sin `pagina:`)
    2  falta un insumo (mazo o JSON de paginacion) / JSON ilegible

Como se emparejan diapositiva y seccion del libro:
    1. `seccion:` del front-matter contra el id / ancla / titulo de la seccion.
    2. si no hay `seccion:`, por titulo normalizado (sin tildes ni puntuacion).
    3. si tampoco empareja, se valida solo que la pagina declarada exista
       dentro del rango de paginas del capitulo.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from construir_presentacion import construir_slides  # reutiliza el parser
except Exception as exc:  # pragma: no cover
    print(f"ERROR: no se pudo importar el parser de diapositivas: {exc}", file=sys.stderr)
    raise SystemExit(2)


def salir(msg: str, codigo: int):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(codigo)


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^0-9a-zA-Z]+", " ", texto).strip().lower()
    return re.sub(r"\s+", " ", texto)


# --------------------------------------------------------------- paginacion
def cargar_paginacion(ruta: Path):
    """Lee capNN-paginas.json con tolerancia de formato.

    Acepta, entre otras formas:
      {"secciones":[{"id":"...","titulo":"...","pagina":12}, ...]}
      {"paginas":{"tipos-de-biofertilizante":12, ...}}
      [{"titulo":"...","pagina_inicio":12}, ...]
      {"titulo-seccion": 12, ...}
    Devuelve (secciones, pagina_min, pagina_max) donde cada seccion es
    {"clave","titulo","pagina"}.
    """
    if not ruta.exists():
        salir(
            f"falta la paginacion del libro: {ruta}\n"
            "       Ese archivo lo produce el constructor del libro.\n"
            "       Genera primero el libro del capitulo y volve a correr esto.",
            2)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        salir(f"{ruta} no es JSON valido ({exc.lineno}:{exc.colno}): {exc.msg}", 2)

    crudo = datos
    if isinstance(datos, dict):
        for clave in ("secciones", "paginas", "indice", "sections", "items"):
            if clave in datos:
                crudo = datos[clave]
                break

    secciones = []
    if isinstance(crudo, dict):
        for k, v in crudo.items():
            if isinstance(v, dict):
                pag = v.get("pagina", v.get("pagina_inicio", v.get("page")))
                titulo = v.get("titulo", v.get("title", k))
            else:
                pag, titulo = v, k
            try:
                secciones.append({"clave": str(k), "titulo": str(titulo), "pagina": int(pag)})
            except (TypeError, ValueError):
                continue
    elif isinstance(crudo, list):
        for it in crudo:
            if not isinstance(it, dict):
                continue
            pag = it.get("pagina", it.get("pagina_inicio", it.get("page", it.get("desde"))))
            titulo = it.get("titulo", it.get("title", it.get("nombre", "")))
            clave = it.get("id", it.get("ancla", it.get("slug", titulo)))
            try:
                secciones.append({"clave": str(clave), "titulo": str(titulo), "pagina": int(pag)})
            except (TypeError, ValueError):
                continue
    else:
        salir(f"{ruta}: no reconozco la estructura (esperaba lista o mapa de secciones)", 2)

    if not secciones:
        salir(f"{ruta}: no contiene ninguna seccion con pagina", 2)

    paginas = [s["pagina"] for s in secciones]
    minima, maxima = min(paginas), max(paginas)
    if isinstance(datos, dict):
        try:
            minima = int(datos.get("pagina_inicio", datos.get("desde", minima)))
            maxima = int(datos.get("pagina_fin", datos.get("hasta", maxima)))
        except (TypeError, ValueError):
            pass
    return secciones, minima, maxima


def buscar_seccion(s, secciones):
    """Devuelve (seccion|None, criterio)."""
    if s.seccion:
        objetivo = normalizar(s.seccion)
        for sec in secciones:
            if normalizar(sec["clave"]) == objetivo or normalizar(sec["titulo"]) == objetivo:
                return sec, "seccion:"
    if s.titulo:
        objetivo = normalizar(s.titulo)
        for sec in secciones:
            if normalizar(sec["titulo"]) == objetivo or normalizar(sec["clave"]) == objetivo:
                return sec, "titulo"
        for sec in secciones:   # coincidencia parcial, ultimo recurso
            nt = normalizar(sec["titulo"])
            if nt and (nt in objetivo or objetivo in nt):
                return sec, "titulo~"
    return None, "—"


# ---------------------------------------------------------------- reporte
def recortar(texto, n):
    texto = str(texto or "")
    return texto if len(texto) <= n else texto[: n - 1] + "…"


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Verifica que cada diapositiva apunte a la pagina real del libro.")
    ap.add_argument("--capitulo", help="p.ej. cap01")
    ap.add_argument("--diapositivas", help="ruta explicita al .md de diapositivas")
    ap.add_argument("--paginas", help="ruta explicita al capNN-paginas.json")
    ap.add_argument("--tolerancia", type=int, default=0,
                    help="paginas de diferencia aceptadas (default 0)")
    args = ap.parse_args(argv)

    if not args.capitulo and not (args.diapositivas and args.paginas):
        salir("indica --capitulo capNN, o bien --diapositivas y --paginas", 2)

    if args.diapositivas:
        mazo = Path(args.diapositivas).expanduser().resolve()
    else:
        mazo = RAIZ / "contenido" / "capitulos" / args.capitulo / "05-diapositivas.md"
    if args.paginas:
        json_pags = Path(args.paginas).expanduser().resolve()
    else:
        json_pags = RAIZ / "salidas" / "libro" / f"{args.capitulo}-paginas.json"

    if not mazo.exists():
        salir(f"falta el mazo de diapositivas: {mazo}", 2)

    secciones, pag_min, pag_max = cargar_paginacion(json_pags)
    slides = construir_slides(mazo.read_text(encoding="utf-8"), 10**9, mazo.parent)
    if not slides:
        salir(f"{mazo}: no contiene diapositivas con front-matter", 2)

    print(f"Mazo      : {mazo}")
    print(f"Paginacion: {json_pags}  ({len(secciones)} secciones, paginas {pag_min}–{pag_max})")
    print()

    cab = f"{'Diap.':>5}  {'Titulo':<34}  {'Declarada':>9}  {'Real':>6}  {'Seccion del libro':<28}  Estado"
    print(cab)
    print("-" * len(cab))

    desfases = 0
    sin_pagina = 0
    emparejadas = 0
    for s in slides:
        sec, criterio = buscar_seccion(s, secciones)
        if sec:
            emparejadas += 1
        declarada = s.pagina
        real = sec["pagina"] if sec else None
        nombre_sec = recortar(sec["titulo"] or sec["clave"], 28) if sec else "(sin emparejar)"

        if declarada is None:
            estado = "SIN PAGINA"
            sin_pagina += 1
        elif real is not None:
            if abs(declarada - real) <= args.tolerancia:
                estado = "OK"
            else:
                estado = f"DESFASE ({declarada - real:+d})"
                desfases += 1
        elif pag_min <= declarada <= pag_max:
            estado = "OK (rango)"
        else:
            estado = f"DESFASE (fuera de {pag_min}–{pag_max})"
            desfases += 1

        print(f"{s.slide:>5}  {recortar(s.titulo or s.layout, 34):<34}  "
              f"{(declarada if declarada is not None else '—'):>9}  "
              f"{(real if real is not None else '—'):>6}  "
              f"{nombre_sec:<28}  {estado}"
              + (f"   [{criterio}]" if sec and criterio != "titulo" else ""))

    print()
    total = len(slides)
    print(f"Emparejadas con una seccion concreta: {emparejadas}/{total}. "
          "El resto solo se valida contra el rango de paginas del capitulo "
          "(agrega `seccion:` al front-matter para verificarlas una por una).")
    if desfases or sin_pagina:
        if desfases:
            print(f"RESULTADO: {desfases}/{total} diapositivas DESFASADAS respecto del libro.")
        if sin_pagina:
            print(f"RESULTADO: {sin_pagina}/{total} diapositivas sin `pagina:` en el front-matter.")
        print("Corregi el `pagina:` del front-matter (o regenera el libro) y volve a verificar.")
        return 1
    print(f"RESULTADO: OK — las {total} diapositivas estan sincronizadas con el libro.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
