#!/usr/bin/env python3
"""Transcribe instantes SVG (capturados con `capturar_gsap.js`) a rejillas de texto.

Es el paso de la Parte A2 del metodo: la fuente es codigo, no video. Cada SVG se
rasteriza sobre un "mundo" fijo, alineado a la reticula de Clawd, y cada celda
toma la tinta que cubre la mayor parte de su area. Asi un tween (rotacion,
estiramiento, desplazamiento) se vuelve pixel art sin que nadie redibuje nada.

Salida: una lista de rejillas del tamano del mundo. `recortar()` las separa en
poses unicas + desplazamientos, que es lo que se guarda en la receta.

Decisiones
----------
K = 6 px por unidad SVG   con U = 16/3, una celda mide 32 px exactos: los
                           bloques caen en pixeles enteros y el conteo es exacto.
mayoria, no centro         un borde rotado 3 grados pasa por el centro de media
                           fila de celdas; el centro parpadea, la mayoria no.
transparente gana empates  una celda cubierta a medias no se pinta: el
                           contorno no engorda al moverse.
"""
import io
import re

import numpy as np

U = 16 / 3
K = 6


def _raster(svg, mundo):
    import cairosvg
    from PIL import Image
    x, y, w, h = mundo
    interior = re.sub(r'^<svg[^>]*>|</svg>\s*$', '', svg.strip())
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" '
           f'width="{round(w * K)}" height="{round(h * K)}" '
           f'shape-rendering="crispEdges">{interior}</svg>')
    png = cairosvg.svg2png(bytestring=doc.encode())
    return np.array(Image.open(io.BytesIO(png)).convert('RGBA')).astype(int)


def transcribir(svg, tintas, x0, y0, columnas, filas, tolerancia=40, u=U,
                metodo='mayoria', ojo_rigido=None, relleno='#'):
    """Un SVG -> rejilla de texto.

    tintas   dict  '#rrggbb' -> caracter
    x0, y0   esquina superior izquierda del mundo, en unidades SVG. Tiene que
             caer en una frontera de celda de la pose de referencia.
    u        lado de la celda en unidades SVG. U para el personaje; 5 para los
             accesorios dibujados en reticula de 5 px (confeti, bandera).
    metodo   'mayoria' para fuentes con rotaciones (tweens); 'centro' para
             dibujos que solo se desplazan: con bordes a media celda en los dos
             ejes, la mayoria de area se come esquinas y el centro no.
    ojo_rigido  caracter del ojo (p. ej. '@') para forzarlo a 2x2 celdas; solo
             para ojos cuadrados de 2U, no para los "^ ^" de la bandera.
    """
    mundo = (x0, y0, columnas * u, filas * u)
    a = _raster(svg, mundo)
    lado = round(u * K)
    a = a[:filas * lado, :columnas * lado]
    colores = [(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)), ch)
               for h, ch in tintas.items()]
    # clase por pixel: 0 = transparente, 1..n = tinta mas cercana
    clase = np.zeros(a.shape[:2], dtype=int)
    mejor = np.full(a.shape[:2], 10 ** 9)
    for i, (rgb, _) in enumerate(colores, start=1):
        d = np.abs(a[..., :3] - np.array(rgb)).sum(2)
        tomar = (d < mejor) & (d <= tolerancia * 3)
        clase[tomar], mejor[tomar] = i, d[tomar]
    clase[a[..., 3] < 128] = 0
    mapa = ['.'] + [ch for _, ch in colores]
    if metodo == 'centro':
        c = lado // 2
        gana = clase[c::lado, c::lado][:filas, :columnas]
        return [''.join(mapa[v] for v in fila) for fila in gana]
    # conteo por bloque de celda
    b = clase.reshape(filas, lado, columnas, lado).transpose(0, 2, 1, 3)
    b = b.reshape(filas, columnas, lado * lado)
    cuentas = np.stack([(b == i).sum(2) for i in range(len(colores) + 1)], 2)
    gana = cuentas.argmax(2)
    # mayoria real: si la tinta ganadora no cubre la mitad, la celda queda vacia
    gana[cuentas.max(2) * 2 < lado * lado] = 0
    if ojo_rigido:
        _ojos_rigidos(gana, clase, mapa.index(ojo_rigido), mapa.index(relleno), lado)
    return [''.join(mapa[c] for c in fila) for fila in gana]


def _ojos_rigidos(gana, clase, i_ojo, i_relleno, lado):
    """Cada ojo vuelve a ser un bloque de 2x2 celdas centrado donde esta en la fuente.

    Con el cuerpo rotado, el ojo de 2U cae en celdas partidas y sale en L o de
    una celda. En Clawd el ojo siempre mide 2U x 2U: se mide su centro en el
    raster y se pinta el bloque entero ahi.
    """
    ys, xs = np.where(clase == i_ojo)
    gana[gana == i_ojo] = i_relleno
    if len(xs) == 0:
        return
    # los ojos son dos grupos separados en x: se corta en el hueco mas grande
    orden = np.sort(np.unique(xs))
    saltos = np.diff(orden)
    grupos = [orden] if len(saltos) == 0 or saltos.max() <= lado else \
        np.split(orden, [int(saltos.argmax()) + 1])
    for g in grupos:
        sel = (xs >= g.min()) & (xs <= g.max())
        cx, cy = xs[sel].mean() / lado, ys[sel].mean() / lado
        c0, f0 = int(round(cx - 1)), int(round(cy - 1))
        gana[max(f0, 0):f0 + 2, max(c0, 0):c0 + 2] = i_ojo


def recortar(rejilla):
    """Rejilla del mundo -> (pose recortada, columna, fila). Vacia -> None."""
    filas = [j for j, f in enumerate(rejilla) if set(f) != {'.'}]
    if not filas:
        return None
    cols = [i for f in rejilla for i, ch in enumerate(f) if ch != '.']
    c0, c1 = min(cols), max(cols) + 1
    fs = [rejilla[j][c0:c1] for j in range(filas[0], filas[-1] + 1)]
    return '\n'.join(fs), c0, filas[0]


# --------------------------------------------------------------------------
# por piezas: poligonos capturados con GEOMETRIA=1 en capturar_gsap.js
# --------------------------------------------------------------------------

def _dentro(px, py, pts):
    """Centros (px, py) dentro del cuadrilatero convexo pts."""
    # orientacion del poligono por su area con signo (horario o antihorario)
    area = sum(ax * by - bx * ay for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]))
    signo = 1 if area >= 0 else -1
    res = np.ones(px.shape, bool)
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        c = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        res &= c * signo >= -1e-9
    return res


def _tramo_en_y(pts, y):
    """Interseccion horizontal del poligono con la recta y: (x_min, x_max) o None."""
    xs = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if (ay - y) * (by - y) <= 0 and ay != by:
            xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
    return (min(xs), max(xs)) if xs else None


def piezas_a_rejilla(captura, tintas, x0, y0, columnas, filas, u=U,
                     ojo='black', lado_angosto=11, cuerpo_id='bdy', patas_min=2,
                     ojos_reposo=None, agacharse_desde=None):
    """Pinta pieza por pieza con reglas de pixel art en vez de muestrear la imagen.

    captura  lo que escribe `capturar_gsap.js` con GEOMETRIA=1: {'piezas': [...],
             'ancla': [x, y] o None}

    Reglas (cada una corrige un error visto en el paseo):
    - ancla        el personaje entero se mueve en celdas enteras.
    - cuerpo rigido  el cuerpo (id `cuerpo_id`) no se deforma al inclinarse:
                   mide siempre round(lado / u) celdas y solo se desplaza. Manos y
                   ojos se colocan en su posicion SIN la rotacion del cuerpo y con
                   el mismo redondeo que el cuerpo, asi no se despegan ni cambian
                   la banda de brazos de 20 a 19 o 21.
    - ojos         bloques de 2x2.
    - patas        (lado corto = `lado_angosto`) 2 celdas de ancho, pegadas justo
                   debajo del cuerpo y hasta donde llega la pata en la fuente o el
                   suelo, con al menos `patas_min` filas: en la demo la pata se
                   encoge y se despega del cuerpo, y en pixel art desaparecia.
                   Una pata inclinada se dibuja recta y corrida entera hacia su
                   lado: un escalon a media pata se veia demasiado diagonal.
    - recorte      (suelo) limita hasta donde llega una pata.
    - agacharse    (opcional) si el centro de los ojos baja `agacharse_desde`
                   unidades o mas respecto a `ojos_reposo` (medido desde el borde
                   de arriba del cuerpo), cuerpo, manos y ojos bajan una fila y las
                   patas quedan una fila mas cortas: al mirar abajo se agacha.
    """
    piezas, ancla = captura['piezas'], captura.get('ancla')
    fx = fy = 0.0
    if ancla:
        fx = ancla[0] - round(ancla[0] / u) * u
        fy = ancla[1] - round(ancla[1] / u) * u
    mover = lambda pts: [(x - fx, y - fy) for x, y in pts]
    g = np.full((filas, columnas), '.', dtype='<U1')

    def lados(pts):
        ax, ay = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        bx, by = pts[3][0] - pts[0][0], pts[3][1] - pts[0][1]
        return (ax, ay), (bx, by), np.hypot(ax, ay), np.hypot(bx, by)

    def rect(c0, f0, n_c, n_f, ch, solo_vacias=False):
        for f in range(max(f0, 0), min(f0 + n_f, filas)):
            for c in range(max(c0, 0), min(c0 + n_c, columnas)):
                if not solo_vacias or g[f, c] == '.':
                    g[f, c] = ch

    # cuerpo: centro, angulo y redondeo que comparten las piezas que van pegadas a el
    cuerpo = next((pz for pz in piezas if pz.get('id') == cuerpo_id), None)
    if cuerpo:
        pts_c = mover(cuerpo['pts'])
        (ax, ay), _, ancho_c, alto_c = lados(pts_c)
        cbx, cby = np.mean(pts_c, axis=0)
        ang = np.arctan2(ay, ax)
        n_c, n_f = round(ancho_c / u), round(alto_c / u)
        rx, ry = (cbx - x0) / u - n_c / 2, (cby - y0) / u - n_f / 2
        aj_x, aj_y = round(rx) - rx, round(ry) - ry
        fila_bajo_cuerpo = int(round(ry + aj_y)) + n_f
    else:
        cbx = cby = ang = aj_x = aj_y = 0.0
        fila_bajo_cuerpo = None

    def sin_rotar(x, y):
        """Posicion de un punto del cuerpo como si el cuerpo no estuviera rotado."""
        dx, dy = x - cbx, y - cby
        c, s_ = np.cos(-ang), np.sin(-ang)
        return cbx + dx * c - dy * s_, cby + dx * s_ + dy * c

    # agacharse al mirar abajo: se mide la bajada de los ojos dentro del cuerpo
    if cuerpo and agacharse_desde is not None:
        ojos_y = [sin_rotar(*np.mean(mover(pz['pts']), axis=0))[1]
                  for pz in piezas if pz['fill'] == ojo]
        if ojos_y and np.mean(ojos_y) - (cby - alto_c / 2) - ojos_reposo >= agacharse_desde:
            aj_y += 1
            fila_bajo_cuerpo += 1

    patas, ajuste_patas = [], None
    for pz in piezas:
        pts, fill = mover(pz['pts']), pz['fill']
        _, _, ancho, alto = lados(pts)
        if abs(ancho - lado_angosto) < 1 and pz is not cuerpo and fill != ojo:
            patas.append(pz)
            continue
        mx, my = np.mean(pts, axis=0)
        if cuerpo and pz is not cuerpo:
            mx, my = sin_rotar(mx, my)
        if fill == ojo:
            n_c_p = n_f_p = 2
        else:
            n_c_p, n_f_p = max(1, round(ancho / u)), max(1, round(alto / u))
        c0 = int(round((mx - x0) / u - n_c_p / 2 + aj_x))
        f0 = int(round((my - y0) / u - n_f_p / 2 + aj_y))
        rect(c0, f0, n_c_p, n_f_p, tintas[fill])

    for pz in patas:
        pts, fill = mover(pz['pts']), pz['fill']
        arriba = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
        abajo = ((pts[2][0] + pts[3][0]) / 2, (pts[2][1] + pts[3][1]) / 2)
        if abajo[1] < arriba[1]:
            arriba, abajo = abajo, arriba
        fondo = abajo[1]
        if pz.get('recorte'):
            fondo = min(fondo, max(p[1] for p in mover(pz['recorte'])))
        # la pata se dibuja recta y corrida entera hacia donde se inclina (como en
        # el original), no con un escalon: se toma la x a media pata
        rx = ((arriba[0] + abajo[0]) / 2 - x0) / u - 1
        if ajuste_patas is None:
            ajuste_patas = round(rx) - rx
        c0 = int(round(rx + ajuste_patas))
        f_ini = fila_bajo_cuerpo if fila_bajo_cuerpo is not None             else int(round((arriba[1] - y0) / u))
        f_fin = int(np.ceil((fondo - y0) / u - 0.5)) - 1        # ultima fila cuyo centro cae en la pata
        if pz.get('recorte'):
            suelo = int(np.floor((max(p[1] for p in mover(pz['recorte'])) - y0) / u)) - 1
        else:
            suelo = filas - 1
        f_fin = min(max(f_fin, f_ini + patas_min - 1), suelo)
        n = f_fin - f_ini + 1
        if n <= 0:
            continue
        rect(c0, f_ini, 2, n, tintas[fill], solo_vacias=True)
    return [''.join(fila) for fila in g]
