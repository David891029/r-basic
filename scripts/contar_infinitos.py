#!/usr/bin/env python3
"""
contar_infinitos.py
-------------------
Estima cuantos simbolos de infinito (∞) aparecen en una imagen, como el patron
del guante de portero.

NOTA IMPORTANTE: el patron del guante es "multiescala" (hay simbolos grandes,
medianos y diminutos anidados unos en otros). Por eso NO existe un unico numero
exacto: el conteo depende de a partir de que tamano consideramos que un dibujo
"cuenta" como simbolo. El parametro --minr controla ese tamano minimo.

Algoritmo:
  1. Se aisla la zona del guante (se descarta el fondo verde y el borde blanco).
  2. Se binariza la textura con umbral adaptativo (invariante al color azul /
     naranja), de modo que los motivos claros quedan en blanco.
  3. Cada simbolo ∞ esta formado por DOS lobulos circulares. Se localizan los
     lobulos como maximos locales de la transformada de distancia y, como cada
     ∞ son dos lobulos, los simbolos ~= lobulos / 2.

Uso:
    python3 scripts/contar_infinitos.py imagen.jpeg [--minr 4] [--debug out.png]
"""
import argparse
import cv2
import numpy as np


def mascara_guante(bgr):
    """Mascara (255 dentro del guante) descartando fondo verde y borde blanco."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    verde = ((h >= 35) & (h <= 90) & (s > 60)).astype(np.uint8) * 255
    blanco = ((s < 40) & (v > 180)).astype(np.uint8) * 255
    guante = cv2.bitwise_not(cv2.bitwise_or(verde, blanco))
    guante = cv2.morphologyEx(guante, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    guante = cv2.morphologyEx(guante, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(guante)
    if n > 1:
        mayor = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        guante = (lab == mayor).astype(np.uint8) * 255
    return guante


def localizar_lobulos(dist, minr):
    """Maximos locales de la transformada de distancia con radio >= minr."""
    k = int(minr * 2) | 1
    dil = cv2.dilate(dist, np.ones((k, k), np.uint8))
    ys, xs = np.where((dist == dil) & (dist >= minr))
    pts = sorted(zip(xs, ys), key=lambda p: -dist[p[1], p[0]])
    keep = []
    r2 = (minr * 1.5) ** 2
    for x, y in pts:
        if all((x - kx) ** 2 + (y - ky) ** 2 >= r2 for kx, ky in keep):
            keep.append((int(x), int(y)))
    return keep


def contar(path, minr=4, debug=None):
    bgr = cv2.imread(path)
    if bgr is None:
        raise SystemExit(f"No pude leer la imagen: {path}")
    guante = mascara_guante(bgr)
    gris = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    binar = cv2.adaptiveThreshold(gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 21, -5)
    binar = cv2.bitwise_and(binar, guante)
    dist = cv2.distanceTransform(binar, cv2.DIST_L2, 5)

    lobulos = localizar_lobulos(dist, minr)
    simbolos = len(lobulos) // 2  # cada ∞ = 2 lobulos

    if debug:
        vis = bgr.copy()
        for x, y in lobulos:
            cv2.circle(vis, (x, y), 3, (0, 0, 255), -1)
        cv2.imwrite(debug, vis)

    return simbolos, len(lobulos)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Estima simbolos de infinito (∞) en una imagen")
    ap.add_argument("imagen")
    ap.add_argument("--minr", type=int, default=4,
                    help="radio minimo del lobulo en px (mas alto = solo simbolos grandes)")
    ap.add_argument("--debug", help="guardar imagen anotada con los lobulos detectados")
    a = ap.parse_args()
    simbolos, lobulos = contar(a.imagen, a.minr, a.debug)
    print(f"Lobulos detectados: {lobulos}")
    print(f"Simbolos de infinito (∞) estimados: ~{simbolos}")
    print("(estimacion aproximada: el patron es multiescala, ajusta --minr para "
          "contar simbolos mas grandes o mas pequenos)")
