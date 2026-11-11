#!/usr/bin/env python3
"""
Genera las figuras botanicas del libro como SVG vectorial.

Las raices y la red de hifas se dibujan por ramificacion recursiva con
azar sembrado (semilla fija), no a mano: por eso se ven organicas y no
como arcos sueltos, y por eso el resultado es identico en cada corrida.

    python3 build/scripts/generar_figuras.py --capitulo cap01
"""
import argparse, math, random
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
V = {"verde9": "#0C3F28", "verde7": "#14633F", "verde4": "#4E9B6E",
     "tierra7": "#9A5C13", "tierra5": "#D08A2C", "tinta": "#1A2420",
     "suave": "#5A6560", "linea": "#D8D2C4"}


def rama(x, y, ang, largo, grosor, prof, rnd, salida, color, nivel_max=4,
         curva=0.42, hijos=(2, 3)):
    """Dibuja una rama como curva de Bezier y se llama a si misma."""
    if prof > nivel_max or largo < 7 or grosor < 0.35:
        return
    desv = rnd.uniform(-curva, curva)
    x2 = x + math.cos(ang) * largo
    y2 = y + math.sin(ang) * largo
    cx = x + math.cos(ang + desv) * largo * 0.55
    cy = y + math.sin(ang + desv) * largo * 0.55
    salida.append(
        f'<path d="M{x:.1f} {y:.1f} Q{cx:.1f} {cy:.1f} {x2:.1f} {y2:.1f}" '
        f'stroke="{color}" stroke-width="{grosor:.2f}" fill="none" stroke-linecap="round"/>')
    n = rnd.randint(*hijos)
    for i in range(n):
        abrir = rnd.uniform(0.22, 0.72) * (1 if i % 2 == 0 else -1)
        rama(x2, y2, ang + abrir + rnd.uniform(-0.12, 0.12),
             largo * rnd.uniform(0.6, 0.78), grosor * 0.66, prof + 1, rnd,
             salida, color, nivel_max, curva, hijos)


def sistema_radical(cx, suelo, rnd, color, escala=1.0):
    s = []
    rama(cx, suelo, math.pi / 2, 62 * escala, 5.2 * escala, 0, rnd, s, color)
    for lado in (-1, 1):
        for k in range(2):
            rama(cx, suelo + 14 + k * 26,
                 math.pi / 2 + lado * rnd.uniform(0.55, 0.95),
                 46 * escala, 3.2 * escala, 1, rnd, s, color)
    return s


def red_hifas(cx, suelo, rnd, color, r_raiz=118):
    """Filamentos que NACEN en el borde de la zona radical y se van hacia
    AFUERA. Ese es el mensaje de la figura: el hongo explora suelo que la
    raiz no toca, no el mismo suelo con mas hilos."""
    s = []
    cy = suelo + 128
    for i in range(30):
        # origen repartido sobre el borde de la zona de la raiz
        a = math.pi * (0.04 + 0.92 * (i / 29)) + rnd.uniform(-0.05, 0.05)
        ox = cx + math.cos(a) * r_raiz * rnd.uniform(0.55, 0.85)
        oy = cy + math.sin(a) * 150 * rnd.uniform(0.35, 0.8) - 40
        # direccion: radial, alejandose del centro de la raiz
        hacia = math.atan2(oy - (cy - 40), ox - cx) + rnd.uniform(-0.2, 0.2)
        rama(ox, oy, hacia, rnd.uniform(52, 78), 1.3, 0, rnd, s, color,
             nivel_max=3, curva=0.5, hijos=(2, 2))
    # esporas en la corona exterior, donde la raiz ya no llega
    for _ in range(18):
        a = rnd.uniform(0.12, math.pi - 0.12)
        r = rnd.uniform(150, 212)
        s.append(f'<circle cx="{cx + math.cos(a) * r:.1f}" '
                 f'cy="{cy - 40 + math.sin(a) * r * 0.72:.1f}" '
                 f'r="{rnd.uniform(2.4, 4.0):.1f}" fill="{color}" opacity=".5"/>')
    return s


def planta(cx, suelo, alto=44, ancho=30):
    return [
        f'<path d="M{cx} {suelo} L{cx} {suelo - alto}" stroke="{V["verde7"]}" '
        f'stroke-width="6" stroke-linecap="round"/>',
        f'<path d="M{cx} {suelo - alto + 12} q{-ancho} -17 {-ancho - 8} -2 '
        f'q{ancho - 8} 18 {ancho + 8} 2z" fill="{V["verde4"]}"/>',
        f'<path d="M{cx} {suelo - alto + 12} q{ancho} -17 {ancho + 8} -2 '
        f'q{-ancho + 8} 18 {-ancho - 8} 2z" fill="{V["verde4"]}"/>',
    ]


def figura_micorriza(destino: Path):
    W, H, SUELO = 940, 540, 110
    izq, der = 232, 700
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" role="img" aria-label="Alcance de la raiz '
        f'sola frente al alcance de la raiz con micorriza">',
        '<defs>',
        '<radialGradient id="zr" cx="50%" cy="18%" r="66%">'
        f'<stop offset="0%" stop-color="{V["verde4"]}" stop-opacity=".26"/>'
        f'<stop offset="100%" stop-color="{V["verde4"]}" stop-opacity=".04"/></radialGradient>',
        '<radialGradient id="zh" cx="50%" cy="18%" r="66%">'
        f'<stop offset="0%" stop-color="{V["tierra5"]}" stop-opacity=".22"/>'
        f'<stop offset="100%" stop-color="{V["tierra5"]}" stop-opacity=".03"/></radialGradient>',
        '</defs>',
        '<g font-family="Source Sans 3, Segoe UI, sans-serif">',
    ]

    # --- izquierda: raiz sola
    out.append(f'<text x="{izq}" y="40" text-anchor="middle" font-size="22" '
               f'font-weight="700" fill="{V["verde9"]}">Raíz sola</text>')
    out.append(f'<ellipse cx="{izq}" cy="{SUELO + 104}" rx="104" ry="126" fill="url(#zr)"/>')
    out.append(f'<line x1="26" y1="{SUELO}" x2="440" y2="{SUELO}" '
               f'stroke="{V["tierra7"]}" stroke-width="3"/>')
    out += planta(izq, SUELO)
    out += sistema_radical(izq, SUELO, random.Random(7), V["verde7"])

    out.append(f'<line x1="470" y1="70" x2="470" y2="470" stroke="{V["linea"]}" '
               f'stroke-width="2" stroke-dasharray="6 7"/>')

    # --- derecha: raiz + micorriza
    out.append(f'<text x="{der}" y="40" text-anchor="middle" font-size="22" '
               f'font-weight="700" fill="{V["verde9"]}">Raíz con micorriza</text>')
    out.append(f'<ellipse cx="{der}" cy="{SUELO + 140}" rx="222" ry="196" fill="url(#zh)"/>')
    out.append(f'<ellipse cx="{der}" cy="{SUELO + 104}" rx="104" ry="126" fill="url(#zr)"/>')
    out.append(f'<line x1="500" y1="{SUELO}" x2="916" y2="{SUELO}" '
               f'stroke="{V["tierra7"]}" stroke-width="3"/>')
    out += red_hifas(der, SUELO, random.Random(21), V["tierra5"])
    out += planta(der, SUELO)
    out += sistema_radical(der, SUELO, random.Random(7), V["verde7"])

    # --- pies
    for x, lineas in ((izq, ["La raíz toma lo que alcanza",
                             "con sus propios pelos."]),
                      (der, ["Las hifas llegan a un volumen de suelo mucho mayor",
                             "y le pasan a la planta fósforo y agua",
                             "que la raíz sola no alcanzaba."])):
        for i, l in enumerate(lineas):
            out.append(f'<text x="{x}" y="{472 + i * 22}" text-anchor="middle" '
                       f'font-size="16" fill="{V["suave"]}">{l}</text>')

    out += ['</g>', '</svg>']
    destino.write_text("\n".join(out) + "\n", encoding="utf-8")
    return destino


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capitulo", default="cap01")
    a = ap.parse_args()
    d = RAIZ / "diseno" / "assets" / a.capitulo
    d.mkdir(parents=True, exist_ok=True)
    print("escrito:", figura_micorriza(d / "fig-micorriza.svg"))


if __name__ == "__main__":
    main()
