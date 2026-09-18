#!/usr/bin/env python3
"""Vectoriza pixel art de forma exacta, sin suavizar las esquinas.

Trazar pixel art con un vectorizador de curvas (vtracer, potrace) redondea los
escalones y arruina justo lo que lo hace pixel art. Aqui se hace al reves: se
detecta la reticula logica, se reduce cada celda a su color dominante y se emiten
rectangulos fusionados. El SVG resultante es exacto — no una aproximacion — y
suele pesar menos que el PNG.

Uso:
    python3 vectorizar_pixelart.py entrada.png salida.svg
    python3 vectorizar_pixelart.py --lote "assets/clawd/*.png" --destino svg/
"""
import argparse, glob, pathlib
import numpy as np
from PIL import Image


def detectar_paso(a, tol_color=0.015):
    """Estima el lado de la celda logica midiendo error de COLOR, no de silueta.

    El error grave de la primera version fue medir solo el canal alfa. La silueta
    de estos dibujos es un blob macizo, asi que una celda muy gruesa la reconstruye
    bien mientras destruye todo el detalle interior —unos audifonos, un sombrero,
    una lupa— sin que la metrica se entere. Aqui se mide la diferencia de color
    dentro del arte, que es lo que de verdad se ve.

    Devuelve (paso, err_color). Si el err_color del mejor paso supera la tolerancia,
    la imagen NO es pixel art recuperable —tipicamente porque fue reescalada con
    resampleo y ya no existe una reticula exacta— y quien llame debe abstenerse de
    vectorizar en vez de emitir un SVG degradado.
    """
    h, w, _ = a.shape
    m = a[:, :, 3] > 128
    if not m.any():
        return 1, 1.0
    mejor, mejor_err = 1, 1.0
    for p in range(3, 41):
        nh, nw = max(1, round(h / p)), max(1, round(w / p))
        chico = Image.fromarray(a.astype('uint8')).resize((nw, nh), Image.BOX)
        grande = np.array(chico.resize((w, h), Image.NEAREST)).astype(float)
        err = np.abs(grande[:, :, :3] - a[:, :, :3])[m].mean() / 255
        # se prefiere la celda mas grande que siga dentro de tolerancia: conserva
        # el caracter de pixel art sin perder detalle
        if err <= tol_color:
            mejor, mejor_err = p, err
        elif mejor == 1 and err < mejor_err:
            mejor, mejor_err = p, err
    return mejor, mejor_err


def reducir(a, paso):
    """Reduce a la reticula logica tomando el color mediano de cada celda."""
    h, w, _ = a.shape
    nh, nw = max(1, round(h / paso)), max(1, round(w / paso))
    ys = np.linspace(0, h, nh + 1).round().astype(int)
    xs = np.linspace(0, w, nw + 1).round().astype(int)
    out = np.zeros((nh, nw, 4), int)
    for i in range(nh):
        for j in range(nw):
            celda = a[ys[i]:ys[i + 1], xs[j]:xs[j + 1]].reshape(-1, 4)
            op = celda[celda[:, 3] > 128]
            if len(op) < len(celda) * 0.4:
                out[i, j] = [0, 0, 0, 0]
            else:
                out[i, j] = np.append(np.median(op[:, :3], axis=0).round(), 255)
    return out


def agrupar_colores(px, tol=26):
    """Junta colores casi iguales; el reescalado deja miles de tonos por ruido."""
    op = px[px[:, :, 3] > 0][:, :3]
    if not len(op):
        return px
    paleta = []
    cols, cuenta = np.unique(op, axis=0, return_counts=True)
    for c in cols[cuenta.argsort()[::-1]]:
        if all(np.linalg.norm(c - p) > tol for p in paleta):
            paleta.append(c)
    paleta = np.array(paleta)
    out = px.copy()
    m = px[:, :, 3] > 0
    d = np.linalg.norm(px[m][:, None, :3] - paleta[None], axis=2)
    out[m, :3] = paleta[d.argmin(1)]
    return out


def rectangulos(mask):
    """Corridas horizontales fusionadas verticalmente cuando coinciden."""
    h, w = mask.shape
    rects, pend = [], {}
    for y in range(h + 1):
        fila = mask[y] if y < h else np.zeros(w, bool)
        corridas, x = [], 0
        while x < w:
            if fila[x]:
                x0 = x
                while x < w and fila[x]:
                    x += 1
                corridas.append((x0, x))
            else:
                x += 1
        nuevas = {}
        for c in corridas:
            if c in pend:
                nuevas[c] = pend.pop(c)
            else:
                nuevas[c] = y
        for (x0, x1), y0 in pend.items():
            rects.append((x0, y0, x1 - x0, y - y0))
        pend = nuevas
    return rects


def vectorizar(entrada, salida, lienzo=None, tol_color=0.015):
    a = np.array(Image.open(entrada).convert('RGBA')).astype(int)
    paso, err = detectar_paso(a.astype(float), tol_color)
    if err > tol_color:
        raise ValueError(
            f"{pathlib.Path(entrada).name}: error de color {err:.1%} sobre la "
            f"tolerancia de {tol_color:.1%} con celda {paso}px. La imagen no es "
            f"pixel art recuperable (probablemente fue reescalada). Vectorizarla "
            f"degradaria el detalle interior — usa el PNG.")
    px = agrupar_colores(reducir(a, paso))
    h, w, _ = px.shape

    piezas = []
    op = px[px[:, :, 3] > 0][:, :3]
    for c in np.unique(op, axis=0):
        m = (px[:, :, 3] > 0) & np.all(px[:, :, :3] == c, axis=2)
        rs = rectangulos(m)
        if not rs:
            continue
        color = "#%02x%02x%02x" % tuple(int(v) for v in c)
        d = "".join(f"M{x} {y}h{ww}v{hh}h{-ww}z" for x, y, ww, hh in rs)
        piezas.append(f'<path fill="{color}" d="{d}"/>')

    # Reja de fidelidad por region de color. El error medio de color puede ser
    # bajo y aun asi tener una tinta entera fuera de lugar: si el 3% de la imagen
    # es el ala de un sombrero y esa tinta cae mal, el promedio apenas se mueve
    # pero el dibujo queda roto. Se exige que CADA tinta coincida con su region en
    # el original.
    peor = 1.0
    for c in np.unique(op, axis=0):
        m_v = (px[:, :, 3] > 0) & np.all(px[:, :, :3] == c, axis=2)
        grande = np.array(Image.fromarray((m_v * 255).astype('uint8'))
                          .resize((a.shape[1], a.shape[0]), Image.NEAREST)) > 127
        m_o = (a[:, :, 3] > 128) & (np.linalg.norm(a[:, :, :3] - c, axis=2) < 60)
        if m_o.sum() < 200:
            continue
        peor = min(peor, (grande & m_o).sum() / max(1, (grande | m_o).sum()))

    lado = lienzo or max(w, h)
    ox, oy = (lado - w) / 2, (lado - h) / 2
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}" '
           f'shape-rendering="crispEdges">\n'
           f'<g transform="translate({ox},{oy})">' + "".join(piezas) + '</g>\n</svg>\n')
    if peor < 0.45:
        raise ValueError(
            f"{pathlib.Path(entrada).name}: una tinta coincide solo {peor:.0%} con "
            f"su region en el original. El dibujo quedaria roto aunque el error "
            f"medio de color sea bajo. Usa el PNG.")
    pathlib.Path(salida).write_text(svg)
    return paso, err, w, h, len(piezas), peor


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("entrada", nargs="?")
    p.add_argument("salida", nargs="?")
    p.add_argument("--lote")
    p.add_argument("--destino", default=".")
    p.add_argument("--lienzo", type=int, default=None,
                   help="lado del viewBox cuadrado; por defecto el lado mayor del arte")
    a = p.parse_args()
    objetivos = ([(f, pathlib.Path(a.destino) / (pathlib.Path(f).stem + ".svg"))
                  for f in sorted(glob.glob(a.lote))] if a.lote
                 else [(a.entrada, a.salida)])
    if a.lote:
        pathlib.Path(a.destino).mkdir(parents=True, exist_ok=True)
    for src, dst in objetivos:
        try:
            paso, err, w, h, n, peor = vectorizar(src, dst, a.lienzo)
            print(f"-> {dst}  celda={paso}px  logico={w}x{h}  "
                  f"error color={err:.2%}  peor tinta={peor:.0%}  capas={n}")
        except ValueError as e:
            print(f"   OMITIDO  {e}")
