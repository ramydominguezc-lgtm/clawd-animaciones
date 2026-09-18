#!/usr/bin/env python3
"""Labels de carga de Claude: la estrella animada + una palabra con brillo ("Thinking…").

No es pixel art ni usa `animar_pixel.py`: es texto. Replica el spinner de Claude
Code tal como esta en su codigo (version 2.1.274, leido del binario instalado):

    estrella   cuadros  · ✢ ✳ ✶ ✻ ✽  de ida y vuelta (12), 120 ms cada uno
    brillo     3 letras en color claro que recorren la palabra de izquierda a
               derecha, un paso cada 50 ms, con 10 posiciones de margen antes y
               despues (ciclo = largo + 20 pasos). En modo "pensando" va de
               derecha a izquierda, un paso cada 200 ms.
    colores    texto y estrella rgb(215,119,87). Brillo rgb(245,149,117) en tema
               claro y rgb(235,159,127) en tema oscuro.
    palabra    verbo + "…". La lista de Claude Code tiene 188 verbos
               ("Clauding", "Pondering"…); "Working" es el de respaldo.

Decisiones
----------
✳ y no *     Claude Code usa ✳ en Ghostty y un * normal en las demas terminales.
             El * de una letra de texto va alto y chico y la estrella "brinca";
             ✳ es de la misma familia que los otros cinco.
ciclo exacto La estrella da la vuelta en 1440 ms y el brillo en (largo+20)x50 ms:
             casi nunca coinciden. Para que el GIF cierre sin salto, el paso del
             brillo se ajusta para que su vuelta dure un multiplo de 1440 ms
             (en "Thinking…", 49.7 ms en vez de 50).
20 ms        Se muestrea cada 20 ms (50 fps): lo minimo que un GIF respeta.

Uso
---
    python label_carga.py "Investigando" DESTINO           un label propio
    python label_carga.py "Pensando" DESTINO --modo pensando
    python label_carga.py --predeterminados DESTINO         el juego base

Opcion --tamano N para la letra en px (default 40).

Donde corre
-----------
Claude Code en Windows (recomendado) y claude.ai web. Fuentes: usa las de
Windows si estan (Cascadia Mono y Segoe UI Symbol, con las que se hicieron los
labels de la biblioteca); si no, las que trae la skill en assets/fuentes
(Cascadia Mono y Noto Sans Symbols 2, ambas OFL). Con Noto la estrella cambia
apenas de trazo. Sin ffmpeg no sale el MP4: se avisa y salen GIF, WebP y HTML.

Cada label sale en DESTINO/<nombre>/: GIF y MP4 en tema claro (fondo crema) y
oscuro, WebP con transparencia por tema, y un bloque HTML autonomo que anima en
vivo (para Claude Design y artifacts).
"""
import argparse
import pathlib
import re
import subprocess
import unicodedata

from PIL import Image, ImageDraw, ImageFont

from animar_pixel import buscar_ffmpeg

FUENTES_SKILL = pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'fuentes'
# la primera que exista: Windows primero (asi se hizo el juego base), luego las de la skill
FUENTE_TEXTO = next(str(f) for f in [pathlib.Path('C:/Windows/Fonts/CascadiaMono.ttf'),
                                     FUENTES_SKILL / 'CascadiaMono-Regular.ttf'] if f.exists())
FUENTE_ESTRELLA = next(str(f) for f in [pathlib.Path('C:/Windows/Fonts/seguisym.ttf'),
                                        FUENTES_SKILL / 'NotoSansSymbols2-Regular.ttf'] if f.exists())
ESTRELLA = ['\u00b7', '\u2722', '\u2733', '\u2736', '\u273b', '\u273d']
CUADROS_ESTRELLA = ESTRELLA + ESTRELLA[::-1]
MS_ESTRELLA = 120
MS_BRILLO = {'solicitando': 50, 'pensando': 200}
MUESTREO_MS = 20

NARANJA = (215, 119, 87)
TEMAS = {
    'claro': {'brillo': (245, 149, 117), 'fondo': (250, 249, 245)},
    'oscuro': {'brillo': (235, 159, 127), 'fondo': (20, 20, 19)},
}

# Juego base. Claude Code elige el verbo al azar entre 188 con la misma
# probabilidad, asi que no hay "mas usados" medibles: se eligieron los estados
# fijos y los verbos que identifican a Claude.
PREDETERMINADOS = [
    ('Thinking', 'pensando'),       # estado fijo cuando el modelo razona
    ('Working', 'solicitando'),     # verbo de respaldo de Claude Code
    ('Researching', 'solicitando'), # modo Research de claude.ai
    ('Clauding', 'solicitando'),    # el verbo propio de Claude
    ('Pondering', 'solicitando'),
    ('Cogitating', 'solicitando'),
    ('Brewing', 'solicitando'),
    ('Noodling', 'solicitando'),
    ('Percolating', 'solicitando'),
    ('Crafting', 'solicitando'),
]


def nombre_archivo(palabra):
    s = unicodedata.normalize('NFKD', palabra).encode('ascii', 'ignore').decode()
    return 'label-' + re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def ciclo(largo, modo):
    """(duracion del bucle en ms, paso del brillo en ms) con cierre exacto."""
    pasos = largo + 20
    vuelta_estrella = MS_ESTRELLA * len(CUADROS_ESTRELLA)
    k = max(1, round(pasos * MS_BRILLO[modo] / vuelta_estrella))
    total = k * vuelta_estrella
    return total, total / pasos


def estado(t, largo, modo, paso):
    """Indice de la estrella y posicion del brillo en el instante t (ms)."""
    i_estrella = int(t // MS_ESTRELLA) % len(CUADROS_ESTRELLA)
    n = int(t // paso) % (largo + 20)
    brillo = n - 10 if modo == 'solicitando' else largo + 10 - n
    return i_estrella, brillo


def render(palabra, modo, tema, tamano=40):
    texto = palabra + '\u2026'
    f_txt = ImageFont.truetype(FUENTE_TEXTO, tamano)
    f_est = ImageFont.truetype(FUENTE_ESTRELLA, tamano)
    celda = f_txt.getlength('M')
    asc, desc = f_txt.getmetrics()
    margen = round(tamano * 0.6)
    ancho = round(margen * 2 + celda * (2 + len(texto)))
    alto = round(margen * 2 + asc + desc)
    ancho += ancho % 2
    alto += alto % 2
    base = margen + asc                          # linea base del texto
    total, paso = ciclo(len(texto), modo)
    brillo_rgb = TEMAS[tema]['brillo']
    cuadros, tiempos = [], []
    for t in range(0, int(total), MUESTREO_MS):
        i_est, g = estado(t, len(texto), modo, paso)
        im = Image.new('RGBA', (ancho, alto), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # estrella centrada a lo ancho en su caja de 2 celdas y sobre la misma
        # linea base que el texto, como la pinta una terminal con fuente de respaldo
        ch = CUADROS_ESTRELLA[i_est]
        cx = margen + celda - f_est.getlength(ch) / 2
        d.text((cx, base), ch, font=f_est, fill=(*NARANJA, 255), anchor='ls')
        for i, c in enumerate(texto):
            color = brillo_rgb if abs(i - g) <= 1 else NARANJA
            d.text((margen + celda * (2 + i), base), c, font=f_txt, fill=(*color, 255), anchor='ls')
        if cuadros and im.tobytes() == cuadros[-1].tobytes():
            tiempos[-1] += MUESTREO_MS
        else:
            cuadros.append(im)
            tiempos.append(MUESTREO_MS)
    return cuadros, tiempos, total


def _plano(im, fondo):
    b = Image.new('RGBA', im.size, (*fondo, 255))
    b.alpha_composite(im)
    return b.convert('RGB')


def exportar(palabra, modo, destino, tamano=40):
    nombre = nombre_archivo(palabra)
    carpeta = pathlib.Path(destino) / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    resumen = {}
    for tema, conf in TEMAS.items():
        cuadros, tiempos, total = render(palabra, modo, tema, tamano)
        base = carpeta / f'{nombre}-{tema}'
        planos = [_plano(c, conf['fondo']) for c in cuadros]
        # una sola paleta para todo el GIF: con paletas por cuadro el brillo parpadea
        mosaico = Image.new('RGB', (planos[0].width, planos[0].height * len(planos)))
        for i, p in enumerate(planos):
            mosaico.paste(p, (0, i * p.height))
        paleta = mosaico.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        gif = [p.quantize(palette=paleta, dither=Image.Dither.NONE) for p in planos]
        # tiempos del GIF en centesimas, redondeados de forma acumulada
        fin, acum = [], 0
        for t in tiempos:
            acum += t
            fin.append(round(acum / 10) * 10)
        t_gif = [b - a for a, b in zip([0] + fin, fin)]
        gif[0].save(f'{base}.gif', save_all=True, append_images=gif[1:], duration=t_gif,
                    loop=0, optimize=False, disposal=1)
        cuadros[0].save(f'{base}.webp', save_all=True, append_images=cuadros[1:],
                        duration=tiempos, loop=0, lossless=True)
        ffmpeg = buscar_ffmpeg()
        if not ffmpeg and tema == 'claro':
            print('AVISO: sin ffmpeg no se generan los MP4 (pip install imageio-ffmpeg lo resuelve)')
        if ffmpeg:
            tmp = carpeta / '_mp4'
            tmp.mkdir(exist_ok=True)
            k, t_acum = 0, 0
            for p, t in zip(planos, tiempos):
                t_acum += t
                while k < round(t_acum * 50 / 1000):
                    p.save(tmp / f'{k:05d}.png')
                    k += 1
            subprocess.run([ffmpeg, '-y', '-v', 'error', '-framerate', '50', '-i', str(tmp / '%05d.png'),
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', f'{base}.mp4'], check=True)
            for f in tmp.iterdir():
                f.unlink()
            tmp.rmdir()
        resumen[tema] = (len(cuadros), total, planos[0].size)
    (carpeta / f'{nombre}-bloque.html').write_text(bloque(palabra, modo), encoding='utf-8', newline='\n')
    return nombre, resumen


def bloque(palabra, modo):
    """HTML autonomo: anima en vivo con la misma logica. Tema con data-tema."""
    texto = palabra + '\u2026'
    total, paso = ciclo(len(texto), modo)
    letras = ''.join(f'<span>{c}</span>' for c in texto)
    cuadros = ''.join(CUADROS_ESTRELLA)
    return f'''<div class="label-carga" data-tema="claro" data-modo="{modo}">
<span class="label-carga__estrella" aria-hidden="true">{CUADROS_ESTRELLA[0]}</span><span class="label-carga__texto">{letras}</span>
</div>
<style>
.label-carga{{--naranja:rgb(215,119,87);--brillo:rgb(245,149,117);display:inline-flex;align-items:baseline;
  font-family:"Cascadia Mono","SF Mono",Menlo,Consolas,monospace;font-size:28px;color:var(--naranja);
  white-space:pre}}
.label-carga[data-tema="oscuro"]{{--brillo:rgb(235,159,127)}}
.label-carga__estrella{{display:inline-block;width:2ch;text-align:center;
  font-family:"Segoe UI Symbol","Apple Symbols","Noto Sans Symbols 2",sans-serif}}
.label-carga__texto span.b{{color:var(--brillo)}}
</style>
<script>
(() => {{
  const raiz = document.currentScript.previousElementSibling.previousElementSibling;
  const estrella = raiz.querySelector('.label-carga__estrella');
  const letras = [...raiz.querySelectorAll('.label-carga__texto span')];
  const cuadros = [...'{cuadros}'];
  const largo = letras.length, total = {total}, paso = {paso:.4f};
  const modo = raiz.dataset.modo;
  const t0 = performance.now();
  (function cuadro(ahora) {{
    const t = (ahora - t0) % total;
    estrella.textContent = cuadros[Math.floor(t / {MS_ESTRELLA}) % cuadros.length];
    const n = Math.floor(t / paso) % (largo + 20);
    const g = modo === 'solicitando' ? n - 10 : largo + 10 - n;
    letras.forEach((l, i) => l.classList.toggle('b', Math.abs(i - g) <= 1));
    requestAnimationFrame(cuadro);
  }})(t0);
}})();
</script>
'''


def main():
    ap = argparse.ArgumentParser(description='Labels de carga de Claude (estrella + palabra con brillo).')
    ap.add_argument('palabra', nargs='?', help='la palabra, sin los tres puntos: "Investigando"')
    ap.add_argument('destino', nargs='?', default='salida')
    ap.add_argument('--modo', choices=list(MS_BRILLO), default='solicitando',
                    help='solicitando: brillo de izquierda a derecha cada 50 ms (default). '
                         'pensando: de derecha a izquierda cada 200 ms.')
    ap.add_argument('--predeterminados', action='store_true', help='genera el juego base')
    ap.add_argument('--tamano', type=int, default=40,
                    help='tamano de letra en px (default 40: ~300 px de ancho para "Thinking…")')
    a = ap.parse_args()
    if a.predeterminados:
        destino = a.palabra or a.destino
        pedidos = PREDETERMINADOS
    elif a.palabra:
        destino, pedidos = a.destino, [(a.palabra, a.modo)]
    else:
        ap.error('falta la palabra o --predeterminados')
    for palabra, modo in pedidos:
        nombre, r = exportar(palabra, modo, destino, a.tamano)
        print(nombre, modo, {t: f'{n} cuadros, {tot / 1000:.2f} s, {tam[0]}x{tam[1]}' for t, (n, tot, tam) in r.items()})


if __name__ == '__main__':
    main()
