#!/usr/bin/env python3
"""
Convierte a JPEG las imagenes del capitulo que son fotografias, y actualiza
las referencias en los markdown.

El material de los docentes trae fotos guardadas como PNG. PNG es el formato
correcto para un diagrama de colores planos, pero para una fotografia pesa
entre cinco y quince veces mas, y ese peso termina incrustado en el PDF: un
capitulo con cuatro fotos asi produce un libro de 15 MB.

No decide por extension ni por nombre: prueba la conversion y se queda con
JPEG solo si ahorra de verdad. Asi los diagramas siguen siendo PNG.

    python3 build/scripts/optimizar_imagenes.py --capitulo cap02
    python3 build/scripts/optimizar_imagenes.py --todos --simular
"""
import argparse, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ANCHO_MAX = 2000          # a 300 dpi cubre 16 cm de ancho impreso
CALIDAD = 88
AHORRO_MINIMO = 0.45      # el JPEG tiene que pesar menos de este % del PNG


def optimizar(cap: str, simular: bool) -> int:
    from PIL import Image
    dir_img = RAIZ / "diseno" / "assets" / cap
    dir_cap = RAIZ / "contenido" / "capitulos" / cap
    if not dir_img.is_dir():
        print(f"  {cap}: no hay imagenes", file=sys.stderr)
        return 0

    renombres, ganado = {}, 0
    for f in sorted(dir_img.iterdir()):
        if f.suffix.lower() != ".png":
            continue
        try:
            im = Image.open(f)
            im.load()
        except Exception as e:
            print(f"  {f.name}: no se pudo abrir ({e})", file=sys.stderr)
            continue

        original = f.stat().st_size
        prueba = im.convert("RGB")
        if prueba.width > ANCHO_MAX:
            alto = round(prueba.height * ANCHO_MAX / prueba.width)
            prueba = prueba.resize((ANCHO_MAX, alto), Image.LANCZOS)

        destino = f.with_suffix(".jpg")
        import io
        buf = io.BytesIO()
        prueba.save(buf, "JPEG", quality=CALIDAD, optimize=True, progressive=True)
        nuevo = buf.getbuffer().nbytes

        if nuevo >= original * AHORRO_MINIMO:
            continue   # es un diagrama: PNG es el formato correcto

        print(f"  {f.name}: {original//1024} KB -> {nuevo//1024} KB  ({destino.name})")
        ganado += original - nuevo
        if not simular:
            destino.write_bytes(buf.getvalue())
            f.unlink()
            renombres[f.name] = destino.name

    if renombres and not simular:
        for md in sorted(dir_cap.glob("*.md")):
            texto = original_texto = md.read_text(encoding="utf-8")
            for viejo, nuevo_n in renombres.items():
                texto = texto.replace(viejo, nuevo_n)
            if texto != original_texto:
                md.write_text(texto, encoding="utf-8")
                print(f"    referencias actualizadas en {md.name}")

    if ganado:
        print(f"  {cap}: {ganado/1024/1024:.1f} MB menos"
              + ("  (simulado)" if simular else ""))
    else:
        print(f"  {cap}: nada que optimizar")
    return ganado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capitulo")
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--simular", action="store_true",
                    help="informa lo que haria, sin tocar archivos")
    a = ap.parse_args()

    if a.todos:
        caps = sorted(d.name for d in (RAIZ / "diseno" / "assets").iterdir() if d.is_dir())
    elif a.capitulo:
        caps = [a.capitulo]
    else:
        print("error: indica --capitulo capNN o --todos", file=sys.stderr)
        return 2

    total = sum(optimizar(c, a.simular) for c in caps)
    print(f"\nTotal: {total/1024/1024:.1f} MB"
          + (" (simulado)" if a.simular else " liberados"))
    print("Volve a construir los capitulos tocados para que los PDF bajen de peso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
