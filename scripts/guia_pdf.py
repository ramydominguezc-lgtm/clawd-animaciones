# Convierte GUIA.md en un PDF con estilo de marca (via Chrome headless).
import base64
import io
import os
import subprocess
import tempfile

import markdown
from PIL import Image, ImageSequence

GUIA = 'C:/Users/alfav/OneDrive/Desktop/Animaciones - Clawd/GUIA.md'
B = 'C:/Users/alfav/OneDrive/Desktop/Clawd - Biblioteca/'
HTML = os.path.join(tempfile.gettempdir(), 'guia_clawd.html')
PDF = 'C:/Users/alfav/OneDrive/Desktop/Guia - Animaciones de Clawd.pdf'


def b64(im):
    buf = io.BytesIO()
    im.save(buf, 'PNG', optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# tira con un cuadro de cada animacion, sobre crema
tiles = []
for n, idx in [('caminando/clawd-caminando', 5), ('saltando/clawd-saltando', 4),
               ('confeti/clawd-confeti', 2), ('pesas/clawd-pesas', 14),
               ('bandera/clawd-bandera', 3), ('paseo/clawd-paseo', 0), ('paseo-arriba/clawd-paseo-arriba', 40)]:
    fr = [f.convert('RGBA').copy() for f in ImageSequence.Iterator(Image.open(B + n + '.webp'))]
    im = fr[min(idx, len(fr) - 1)]
    bbox = im.getbbox()
    im = im.crop((max(bbox[0] - 20, 0), max(bbox[1] - 20, 0), min(bbox[2] + 20, im.width), min(bbox[3] + 20, im.height)))
    im.thumbnail((220, 170), Image.NEAREST)
    base = Image.new('RGBA', (230, 180), (250, 249, 245, 255))
    base.alpha_composite(im, ((230 - im.width) // 2, (180 - im.height) // 2))
    tiles.append(base)
tira = Image.new('RGB', (230 * len(tiles), 180), (250, 249, 245))
for i, t in enumerate(tiles):
    tira.paste(t.convert('RGB'), (i * 230, 0))
muestrario = Image.open(B + 'labels/muestrario.png').convert('RGB')

md = open(GUIA, encoding='utf-8').read()
cuerpo = markdown.markdown(md, extensions=['tables', 'fenced_code'])
cuerpo = cuerpo.replace('<h2>3. Lo que ya existe</h2>',
                        '<h2>3. Lo que ya existe</h2>\n<img class="tira" src="data:image/png;base64,' + b64(tira) +
                        '"><p class="pie">caminando · saltando · confeti · pesas · bandera · paseo · paseo mirando arriba</p>', 1)
cuerpo = cuerpo.replace('<h2>4. Cómo pedir</h2>',
                        '<img class="muestrario" src="data:image/png;base64,' + b64(muestrario) +
                        '"><p class="pie">Labels de carga en tema claro y oscuro</p>\n<h2>4. Cómo pedir</h2>', 1)

html = f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Guía — Animaciones de Clawd</title>
<style>
  @page {{ size: Letter; margin: 17mm 16mm; }}
  body {{ font-family: "Segoe UI", Arial, sans-serif; color:#141413; font-size:10pt; line-height:1.45; }}
  h1 {{ font-size:22pt; margin:0 0 2mm; }}
  h1 + p {{ color:#7d7b74; }}
  h2 {{ font-size:14pt; margin:7mm 0 2.5mm; padding-top:2mm; border-top:2px solid #d97757; page-break-after:avoid; }}
  h3 {{ font-size:11pt; margin:5mm 0 1.5mm; page-break-after:avoid; }}
  table {{ width:100%; border-collapse:collapse; margin:2mm 0 3mm; font-size:9pt; }}
  tr {{ page-break-inside:avoid; }}
  th {{ text-align:left; background:#e8e6dc; padding:1.5mm 2mm; }}
  td {{ padding:1.5mm 2mm; border-bottom:1px solid #e8e6dc; vertical-align:top; }}
  code {{ font-family: Consolas, monospace; font-size:8.6pt; background:#f0eee6; padding:0 1mm; border-radius:2px; }}
  pre {{ background:#f0eee6; padding:3mm; border-radius:3px; white-space:pre-wrap; page-break-inside:avoid; }}
  pre code {{ background:none; padding:0; }}
  blockquote {{ margin:2mm 0; padding:2mm 4mm; border-left:4px solid #d97757; background:#faf9f5; }}
  blockquote p {{ margin:0; }}
  hr {{ display:none; }}
  img.tira, img.muestrario {{ display:block; margin:2mm auto 0; }}
  img.tira {{ width:100%; }}
  img.muestrario {{ width:62%; }}
  .pie {{ text-align:center; color:#7d7b74; font-size:8.5pt; margin-top:1mm; }}
</style></head><body>{cuerpo}</body></html>'''
open(HTML, 'w', encoding='utf-8').write(html)
subprocess.run(['C:/Program Files/Google/Chrome/Application/chrome.exe', '--headless=new', '--disable-gpu',
                '--no-pdf-header-footer', f'--print-to-pdf={PDF}', 'file:///' + HTML], check=True,
               capture_output=True)
print('ok', PDF)
