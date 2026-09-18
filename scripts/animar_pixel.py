#!/usr/bin/env python3
"""Motor de animacion pixel art: de rejillas de texto a todos los formatos.

No sabe nada de Clawd. Recibe poses escritas como texto, una secuencia con
duraciones y una paleta, y devuelve GIF, WebP, MP4, hoja de sprites, PNG y SVG
por pose, CSS, una demo y un bloque HTML autonomo. Para hacer una animacion
nueva se escribe un archivo de datos que llame a `construir()` — ver
`clawd_caminando.py` como ejemplo.

Formato de una pose:  (fila_inicial, "rejilla de texto")

    ('.' es transparente; cualquier otro caracter es una tinta de la paleta)

    POSE = (4, '''
    ..####..
    ..#@@#..
    .######.
    ..#..#..
    ''')

`fila_inicial` es donde empieza la rejilla dentro del lienzo. Es lo que permite
que un personaje suba y baje sin reescribir el dibujo: misma rejilla, otra fila.

Decisiones que parecen detalle y no lo son
------------------------------------------
paleta a mano   Dejar que PIL cuantice mete dither y colores intermedios. En
                pixel art eso se ve como suciedad en los bordes. Aqui la paleta
                se construye indice por indice y no hay color que no pidieras.
GIF doble       La transparencia del GIF es binaria: sobre fondo oscuro deja
                borde. Se exportan las dos versiones y se elige por destino.
SVG en dos ejes Fusionar solo en horizontal da una tira por fila: pinta igual,
                pesa el triple y no se puede leer a mano.
MP4 con fondo   El video no tiene alfa. Se aplana sobre el fondo declarado.
"""
import pathlib
import shutil
import subprocess
from PIL import Image

CREMA = (250, 249, 245)
HOJA_MAX = 16384             # ancho maximo de la hoja de sprites, en px
TRANSPARENTE = '.'


# --------------------------------------------------------------------------
# manipulacion de poses
# --------------------------------------------------------------------------

def filas(pose):
    ini, txt = pose
    return ini, txt.strip('\n').split('\n')


def espejo(pose):
    """Voltea la pose en horizontal. Duplica un ciclo sin volver a dibujarlo."""
    ini, fs = filas(pose)
    return (ini, '\n' + '\n'.join(f[::-1] for f in fs) + '\n')


def desplazar(pose, dy):
    """Sube o baja la pose dentro del lienzo. Asi se hace el rebote."""
    return (pose[0] + dy, pose[1])


def buscar_ffmpeg():
    """Ruta a ffmpeg o None. En claude.ai web puede no estar en el sistema:
    se prueba el paquete `imageio-ffmpeg` (pip), que trae su propio binario."""
    ruta = shutil.which('ffmpeg')
    if ruta:
        return ruta
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def componer(lienzo, capas):
    """Encima capas en un solo lienzo y devuelve una pose nueva.

    capas  list  [(pose, dx, dy), ...] en orden de pintado: la ultima queda
                 encima. dx corre la pose en columnas y dy en filas.

    Sirve para animar partes independientes —un personaje y un efecto que va
    a otro ritmo o en otra posicion— sin redibujar cada combinacion a mano.
    """
    w_u, h_u = lienzo
    g = [['.'] * w_u for _ in range(h_u)]
    for pose, dx, dy in capas:
        ini, fs = filas(pose)
        for j, fila in enumerate(fs):
            y = ini + dy + j
            for i, ch in enumerate(fila):
                x = dx + i
                if ch != TRANSPARENTE and 0 <= y < h_u and 0 <= x < w_u:
                    g[y][x] = ch
    return (0, '\n' + '\n'.join(''.join(f) for f in g) + '\n')


def medir(poses, margen=1):
    """Lienzo minimo que contiene todas las poses, con margen. Devuelve (w, h)."""
    x0 = y0 = 10 ** 6
    x1 = y1 = -1
    for pose in poses.values():
        ini, fs = filas(pose)
        for j, fila in enumerate(fs):
            for x, ch in enumerate(fila):
                if ch != TRANSPARENTE:
                    x0, x1 = min(x0, x), max(x1, x)
                    y0, y1 = min(y0, ini + j), max(y1, ini + j)
    return x1 + 1 + margen, y1 + 1 + margen


# --------------------------------------------------------------------------
# rasterizado
# --------------------------------------------------------------------------

def pintar(pose, paleta, lienzo, escala, fondo=None):
    w_u, h_u = lienzo
    base = (*fondo, 255) if fondo else (0, 0, 0, 0)
    im = Image.new('RGBA', (w_u, h_u), base)
    px = im.load()
    ini, fs = filas(pose)
    for j, fila in enumerate(fs):
        y = ini + j
        if not 0 <= y < h_u:
            continue
        for x, ch in enumerate(fila):
            if ch in paleta and x < w_u:
                px[x, y] = (*paleta[ch], 255)
    return im.resize((w_u * escala, h_u * escala), Image.NEAREST)


def a_svg(pose, paleta, lienzo):
    """SVG exacto: un path por tinta, rectangulos fusionados en los dos ejes."""
    w_u, h_u = lienzo
    ini, fs = filas(pose)
    paths = []
    for ch, rgb in paleta.items():
        corridas = []
        for j, fila in enumerate(fs):
            y, x = ini + j, 0
            while x < len(fila):
                if fila[x] == ch:
                    x0 = x
                    while x < len(fila) and fila[x] == ch:
                        x += 1
                    corridas.append((y, x0, x - x0))
                else:
                    x += 1
        abiertos, d = {}, []
        for y in range(ini, ini + len(fs) + 1):
            en_fila = {(x0, w) for yy, x0, w in corridas if yy == y}
            for k in list(abiertos):
                if k in en_fila:
                    abiertos[k][1] += 1
                else:
                    y0, alto = abiertos.pop(k)
                    d.append(f'M{k[0]} {y0}h{k[1]}v{alto}h-{k[1]}z')
            for k in en_fila - set(abiertos):
                abiertos[k] = [y, 1]
        if d:
            hexa = '#%02x%02x%02x' % rgb
            paths.append(f'<path fill="{hexa}" d="{"".join(d)}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w_u} {h_u}" '
            f'shape-rendering="crispEdges">\n' + '\n'.join(paths) + '\n</svg>\n')


# --------------------------------------------------------------------------
# exportacion
# --------------------------------------------------------------------------

def _a_paleta(im, paleta, fondo, fondo_idx):
    """RGBA -> modo P con paleta explicita. Indice 0 reservado al transparente."""
    idx = {None: 0}
    tabla = [0, 0, 0]
    for i, rgb in enumerate(list(paleta.values()) + [fondo], start=1):
        idx[rgb] = i
        tabla += list(rgb)
    out = Image.new('P', im.size, fondo_idx)
    px, opx = im.load(), out.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = px[x, y]
            if a > 128:
                opx[x, y] = idx.get((r, g, b), fondo_idx)
    out.putpalette(tabla + [0] * (768 - len(tabla)))
    return out


def _css(secuencia, orden, w, h, nombre, tiempo_ms, hoja, por_fila):
    total = sum(t for _, t in secuencia)
    lineas, acum = [], 0
    for clave, t in secuencia:
        i = orden.index(clave)
        x, y = i % por_fila * w, i // por_fila * h
        pos = f'-{x}px 0' if y == 0 else f'-{x}px -{y}px'
        lineas.append(f'  {acum / total * 100:.3f}% {{ background-position: '
                      f'{pos}; }}')
        acum += t
    dur = total * tiempo_ms / 1000
    return (f'/* {nombre} — hoja de {len(orden)} fotogramas de {w}x{h} px.\n'
            f'   Tiempo base: {tiempo_ms} ms por tiempo. Ciclo completo: {dur:.2f} s. */\n'
            f'.{nombre} {{\n  width: {w}px;\n  height: {h}px;\n'
            f'  background-image: url("{hoja}");\n'
            f'  background-repeat: no-repeat;\n'
            f'  image-rendering: pixelated;\n'
            f'  animation: {nombre} {dur:.2f}s step-end infinite;\n}}\n\n'
            f'@keyframes {nombre} {{\n' + '\n'.join(lineas) + '\n}\n')


def _demo(orden, w, h, nombre, tiempo_ms):
    tiras = '\n'.join(
        f'  <img src="fotogramas/{nombre}-{n}.png" alt="{n}" title="{n}">'
        for n in orden)
    return f'''<!doctype html>
<meta charset="utf-8"><title>{nombre}</title>
<link rel="stylesheet" href="{nombre}.css">
<style>
  body {{ margin:0; background:#faf9f5; color:#141413;
         font-family:Poppins,Arial,sans-serif; display:grid; place-items:center;
         min-height:100vh; gap:24px; }}
  .fila {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:center;
           max-width:1100px; }}
  .fila img {{ width:{max(48, w // 4)}px; image-rendering:pixelated;
               background:#f0eee6; }}
  p {{ font-size:13px; color:#7d7b74; margin:0; }}
</style>
<div class="{nombre}"></div>
<p>{len(orden)} fotogramas unicos · tiempo base {tiempo_ms} ms · fondo transparente</p>
<div class="fila">
{tiras}
</div>
'''


def _bloque(poses, orden, secuencia, paleta, lienzo, nombre, tiempo_ms,
            ancho=280):
    """Bloque HTML autonomo: todas las poses en un solo SVG en linea + keyframes.

    Es el formato para canvas, artifacts y Claude Design: no depende de ningun
    archivo externo, asi que pinta aunque la ruta local no resuelva. Para
    escalarlo se cambia solo `width`; `aspect-ratio` y `overflow` no se tocan.
    """
    w_u, h_u = lienzo
    n = len(orden)
    grupos = []
    for i, clave in enumerate(orden):
        paths = a_svg(poses[clave], paleta, lienzo).strip().split('\n')[1:-1]
        grupos.append(f'<g transform="translate({i * w_u} 0)">\n'
                      + '\n'.join(paths) + '\n</g>')
    total = sum(t for _, t in secuencia)
    marcos, acum = [], 0
    for clave, t in secuencia:
        marcos.append(f'{acum / total * 100:.3f}%{{transform:translateX('
                      f'-{orden.index(clave) / n * 100:.4f}%)}}')
        acum += t
    dur = total * tiempo_ms / 1000
    return (f'<div class="{nombre}">\n<svg viewBox="0 0 {w_u * n} {h_u}" '
            f'shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">\n'
            + '\n'.join(grupos) + '\n</svg>\n</div>\n<style>\n'
            f'.{nombre}{{width:{ancho}px;aspect-ratio:{w_u}/{h_u};'
            f'overflow:hidden;position:relative}}\n'
            f'.{nombre} svg{{position:absolute;height:100%;width:auto;\n'
            f'  animation:{nombre} {dur:.2f}s step-end infinite}}\n'
            f'@keyframes {nombre}{{' + ''.join(marcos) + '}\n</style>')


def construir(destino, poses, secuencia, paleta, nombre='animacion',
              lienzo=None, escala=16, fondo=CREMA, tiempo_ms=80, fps_video=60):
    """Escribe todos los formatos en `destino`.

    poses      dict  clave -> (fila_inicial, rejilla de texto)
    secuencia  list  [(clave, tiempos), ...]   tiempos en unidades de tiempo_ms
    paleta     dict  caracter -> (r, g, b)
    lienzo     (w_u, h_u) en unidades de rejilla; si es None se calcula
    """
    destino = pathlib.Path(destino)
    (destino / 'fotogramas').mkdir(parents=True, exist_ok=True)
    (destino / 'svg').mkdir(exist_ok=True)
    lienzo = lienzo or medir(poses)

    orden = []
    for clave, _ in secuencia:
        if clave not in orden:
            orden.append(clave)

    imgs = {n: pintar(poses[n], paleta, lienzo, escala) for n in orden}
    for n in orden:
        imgs[n].save(destino / 'fotogramas' / f'{nombre}-{n}.png')
        (destino / 'svg' / f'{nombre}-{n}.svg').write_text(
            a_svg(poses[n], paleta, lienzo), encoding='utf-8', newline='\n')

    w, h = imgs[orden[0]].size
    # la hoja se parte en filas si pasa de 16384 px: es el limite de ancho de
    # WebP y de muchas GPU; una tira mas larga no pinta en el navegador
    por_fila = min(len(orden), max(1, HOJA_MAX // w))
    n_filas = -(-len(orden) // por_fila)
    hoja = Image.new('RGBA', (w * por_fila, h * n_filas), (0, 0, 0, 0))
    for i, n in enumerate(orden):
        hoja.paste(imgs[n], (i % por_fila * w, i // por_fila * h))
    hoja.save(destino / f'{nombre}-hoja.png')

    # tiempos redondeados de forma acumulada: cada formato tiene su propia
    # rejilla de tiempo (el GIF centesimas, el MP4 1/fps) y redondear cuadro
    # por cuadro hace que el ciclo se alargue o se acorte
    fin_ms = []
    for _, t in secuencia:
        fin_ms.append((fin_ms[-1] if fin_ms else 0) + t * tiempo_ms)
    tiempos = [b - a for a, b in zip([0] + fin_ms, fin_ms)]
    fin_cs = [round(f / 10) * 10 for f in fin_ms]
    tiempos_gif = [b - a for a, b in zip([0] + fin_cs, fin_cs)]
    for sufijo, transp in [('.gif', False), ('-transparente.gif', True)]:
        cuadros = [_a_paleta(imgs[c], paleta, fondo, 0 if transp else
                             len(paleta) + 1) for c, _ in secuencia]
        extra = dict(transparency=0, disposal=2) if transp else {}
        cuadros[0].save(destino / f'{nombre}{sufijo}', save_all=True,
                        append_images=cuadros[1:], duration=tiempos_gif,
                        loop=0, optimize=False, **extra)

    cuadros = [imgs[c] for c, _ in secuencia]
    cuadros[0].save(destino / f'{nombre}.webp', save_all=True,
                    append_images=cuadros[1:], duration=tiempos, loop=0,
                    lossless=True, exact=True)

    ffmpeg = buscar_ffmpeg()
    if not ffmpeg:
        print('AVISO: sin ffmpeg no se genera el MP4 (pip install imageio-ffmpeg lo resuelve)')
    tmp = destino / '_mp4'
    if ffmpeg:
        tmp.mkdir(exist_ok=True)
    if ffmpeg:
        planos = {n: Image.alpha_composite(
            Image.new('RGBA', imgs[n].size, (*fondo, 255)), imgs[n]).convert('RGB')
            for n in orden}
        k = 0
        for (clave, _), fin in zip(secuencia, fin_ms):
            while k < round(fin * fps_video / 1000):
                planos[clave].save(tmp / f'{k:05d}.png')
                k += 1
        subprocess.run([ffmpeg, '-y', '-v', 'error', '-framerate', str(fps_video),
                        '-i', str(tmp / '%05d.png'), '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', '-crf', '18',
                        str(destino / f'{nombre}.mp4')], check=True)
        for f in tmp.iterdir():
            f.unlink()
        tmp.rmdir()

    # utf-8 y saltos \n explicitos: en Windows write_text usa cp1252 y CRLF,
    # y el CSS y la demo salian con los acentos rotos.
    for sufijo, texto in [
            ('.css', _css(secuencia, orden, w, h, nombre, tiempo_ms,
                          f'{nombre}-hoja.png', por_fila)),
            ('.html', _demo(orden, w, h, nombre, tiempo_ms)),
            ('-bloque.html', _bloque(poses, orden, secuencia, paleta, lienzo,
                                     nombre, tiempo_ms))]:
        (destino / f'{nombre}{sufijo}').write_text(texto, encoding='utf-8',
                                                   newline='\n')

    return orden, (w, h), lienzo


def verificar(destino, nombre, orden, escala):
    """Comprueba que cada SVG pinta exactamente lo mismo que su PNG.

    Es la unica prueba que atrapa un SVG mal fusionado: el error tipico no es
    un color raro, es un rectangulo desplazado una fila que a simple vista no
    se nota. Requiere cairosvg.
    """
    import io
    import numpy as np
    import cairosvg
    malos = []
    for n in orden:
        svg = destino / 'svg' / f'{nombre}-{n}.svg'
        png = destino / 'fotogramas' / f'{nombre}-{n}.png'
        ref = Image.open(png)
        dato = cairosvg.svg2png(url=str(svg), output_width=ref.size[0],
                                output_height=ref.size[1])
        a = np.array(Image.open(io.BytesIO(dato)).convert('RGBA')).astype(int)
        b = np.array(ref.convert('RGBA')).astype(int)
        dif = int((np.abs(a - b).sum(2) > 30).sum())
        if dif:
            malos.append((n, dif))
    return malos
