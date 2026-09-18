---
name: clawd-animaciones
description: Generador de animaciones de Claude — pixel art de Clawd (poses medidas, motor por fotogramas, réplica desde código o video) y labels de carga con la estrella animada ("✻ Thinking…"). Úsala para crear, replicar o regenerar una animación de Clawd o un label de carga. Lo terminado se guarda y se entrega desde la skill clawd-biblioteca.
---

# Clawd — generador de animaciones

Clawd se anima **por cuadros, no por interpolación**: entre dos formas de pixel
art no hay tween posible. Todo aquí parte de eso.

**Dos skills enlazadas:**

| Skill | Carpeta | Hace |
|---|---|---|
| `clawd-animaciones` (esta) | `Desktop\Animaciones - Clawd` | Genera: método, motor, recetas |
| `clawd-biblioteca` | `Desktop\Clawd - Biblioteca` | Almacena y entrega: archivos terminados, `CATALOGO.md`, fuentes |

Aquí no se guarda ninguna animación terminada. **Antes de generar, leer el
`CATALOGO.md` de `clawd-biblioteca`**: si ya existe, se entrega desde la
biblioteca y no se gasta nada más.

**Hay una tercera skill que consume de la biblioteca:** `anthro-pic-brand`
(`Desktop\anthro-pic-brand`) compone los posts y mete animaciones en ellos.
Hoy usa `paseo` en su pieza de terminal, en PNG fijo y en MP4. Regenerar `paseo`
cambia esa pieza: avisar antes.

## Dónde corre

Se recomienda **Claude Code en la terminal de la PC de Ramses**, donde está todo
probado. También funciona en **claude.ai web**, con estas diferencias:

| | Claude Code (recomendado) | claude.ai web |
|---|---|---|
| Carpetas | `Desktop\Animaciones - Clawd` y `Desktop\Clawd - Biblioteca` | La carpeta donde está montada cada skill. No hay escritorio |
| Dónde sale lo generado | Directo en la biblioteca | En la carpeta de salida de la conversación, para descargar. Las skills son de solo lectura: lo nuevo **no** queda en la biblioteca hasta volver a subir su ZIP o generarlo en Claude Code |
| Comando | `python` | `python3` |
| GIF, WebP, SVG, hoja, CSS, bloque HTML | Sí | Sí (Pillow y numpy) |
| MP4 | Sí | Solo si hay ffmpeg. Si no hay, probar `pip install imageio-ffmpeg`; si tampoco se puede, el script avisa y entrega lo demás |
| Labels de carga | Sí, con Cascadia Mono y Segoe UI Symbol de Windows | Sí, con las fuentes de `assets/fuentes/` (Cascadia Mono y Noto Sans Symbols 2). La estrella cambia apenas de trazo |
| Verificar SVG (`cairosvg`) | Sí | Si falta, se avisa y se sigue |
| Replicar desde el código de una página | Sí | **No**: necesita Chrome y abrir páginas web |
| Replicar desde video | Sí | Solo si hay ffmpeg |

En claude.ai, al empezar, correr `python3 -c "import PIL, numpy"` y `ffmpeg -version`
para saber qué hay antes de prometer formatos.

## Input — estricto

Cada pedido trae exactamente estos campos. **Si falta uno obligatorio, se
pregunta; no se inventa.**

| Campo | Obligatorio | Valores |
|---|---|---|
| `modo` | sí | `entregar` · `replicar` · `crear` |
| `nombre` | sí | `clawd-<accion>` en minúsculas con guiones: `clawd-confeti` |
| `destino` | sí | web · WhatsApp/Notion · Instagram · sitio propio · Claude Design · pose suelta |
| `fuente` | solo en `replicar` | ruta o URL de la referencia **y** cuál animación dentro de ella |
| `guion` | solo en `crear` | la acción por tiempos (ver abajo) |
| `fondo` | no | crema `#faf9f5` (por defecto). Para blanco u oscuro se entrega el GIF transparente o el WebP; un MP4 sobre oscuro se regenera pasando `fondo=(20, 20, 19)` a `construir()` en la receta. Nunca naranja |

**`guion` (modo `crear`)** — la secuencia de poses, cada una con su duración en
tiempos de 1/12 s, y si hace bucle:

```
caminando.quieto 5 · caminando.parpadeo 1 · confeti.A1 1 · confeti.A2 2 · confeti.A3 1   bucle: sí
```

Cada pose se nombra `archivo.pose`. Poses con nombre para mezclar:

- `caminando.`: `quieto`, `parpadeo`, `frente`, `a1`–`a5`, `b1`–`b5`
- `confeti.`: `AGACHADO`, `A1`–`A3`, `B1`–`B3`

Las dos comparten retícula (28 columnas, patas en 6–21). El suelo está en la
fila 19 en la caminata y en la 25 en el confeti: las de la caminata se bajan 6
filas con `desplazar(pose, 6)`. Las poses de `paseo`, `pesas` y `bandera` son
transcripciones numeradas y **no** se mezclan: `paseo` y `paseo_arriba` además usan otro dibujo
(brazos de 20U). Si el guion pide una pose que no existe, se dibuja sobre la
retícula canónica partiendo de `QUIETO` o `AGACHADO` y **se muestra una hoja de
contactos para aprobarla antes de exportar**.

**Lo que no se pide porque es fijo:** paleta, retícula, carpeta de salida
(`<biblioteca>/<accion>/` en Claude Code; la carpeta de salida en claude.ai) y
verificación.

## Flujo por modo

- **entregar**: es tarea de `clawd-biblioteca`. Si no está en la biblioteca pero
  tiene receta, se regenera aquí hacia la biblioteca.
- **replicar**: `references/animacion-pixel.md`.
  - Si la fuente es **código** (una página con SVG/GSAP), Parte A2:
    1. extraer el módulo;
    2. `capturar_gsap.js` lo corre con el GSAP real y guarda el SVG de cada instante
       (o, con `GEOMETRIA=1`, la geometría de cada pieza si hay rotaciones);
    3. `transcribir_svg.py` lo pasa a la retícula (`transcribir()` o `piezas_a_rejilla()`);
    4. se escribe la receta.
  - Si la fuente es **video**, Parte A.
- **crear**: guion → poses (reusar antes que dibujar) → receta → generar.

En los tres casos se termina así: generar en la biblioteca → verificar → escribir
`LEEME.md` y la comparativa → agregar la fila en `CATALOGO.md`.

Generar, desde la carpeta de esta skill: `python scripts/clawd_<accion>.py <destino>/<accion>`
(`<destino>` es la biblioteca en Claude Code, `C:\Users\alfav\OneDrive\Desktop\Clawd - Biblioteca`,
o la carpeta de salida en claude.ai).

**Verificación mínima antes de entregar:**
- `SVG infieles: ninguno` en la salida del script.
- IoU de silueta contra la fuente, con las diferencias explicadas en el `LEEME`.
- Comparativa lado a lado guardada junto a la animación.
- Cada formato decodificado y mirado.

## Labels de carga (aparte del pixel art)

La estrella animada con palabra que brilla (`✻ Thinking…`). No usa el motor de
pixel art: es texto, con su propio script. Especificación leída del código de
Claude Code en `references/labels-carga.md`.

**Input estricto:** `palabra` (sin los tres puntos) y, opcionalmente, `modo`
(`solicitando` por defecto, o `pensando`) y `tamano` (px de letra, 40 por
defecto). Antes de generar, revisar `labels/` en `clawd-biblioteca`: hay 10 hechos.

```
python scripts/label_carga.py "Investigando" <destino>/labels [--modo pensando] [--tamano 64]
python scripts/label_carga.py --predeterminados <destino>/labels
```

Salen GIF y MP4 claro y oscuro, WebP transparente por tema y bloque HTML en vivo.

## El personaje no se dibuja a ojo

Retícula canónica, confirmada por la captura de la caminata y por el SVG de las
demos: **cuerpo 16U, banda de brazos 24U, ojos 2U×2U, patas 2U**, con U = 16/3 px
en las demos. Dibujar a ojo sobre una retícula inventada da proporciones
sistemáticamente equivocadas.

Colores: cuerpo `#d97757`, sombra `#b8654a`, ojo `#141413`. La sombra es el
naranja × 0.85: una razón medida, no un criterio. Los colores de capturas o
demos (`#d46c4d`, `#DD775B`) no se usan para Clawd. Los objetos (confeti,
mancuerna, bandera) conservan los hex de su fuente.

**En pixel art no hay media celda.** Cuando la fuente mueve algo fracciones de
unidad, se redondea el desplazamiento a celdas enteras y la pieza se transcribe
una sola vez (confeti, bandera). Cuando rota, se transcribe cuadro por cuadro
por piezas desde su geometría exacta: cada pieza con tamaño fijo, el cuerpo sin rotar y las patas rectas corridas hacia su lado (paseo).

## Archivos

| Qué | Dónde |
|---|---|
| Método: video (A), código (A2), dibujo (B), destinos (C) | `references/animacion-pixel.md` |
| Motor (no sabe nada de Clawd) | `scripts/animar_pixel.py` |
| Captura de componentes SVG+GSAP en Chrome | `scripts/capturar_gsap.js` + `gsap.min.js` (3.14.2) |
| SVG → rejilla de texto | `scripts/transcribir_svg.py` |
| Vectorizador de pixel art exacto | `scripts/vectorizar_pixelart.py` |
| Labels de carga: script y especificación | `scripts/label_carga.py` · `references/labels-carga.md` |
| Recetas | `scripts/clawd_caminando.py` · `clawd_saltando.py` · `clawd_confeti.py` · `clawd_paseo.py` · `clawd_paseo_arriba.py` · `clawd_pesas.py` · `clawd_bandera.py` |
| Guía para quien pide (input, alcances, limitaciones) | `GUIA.md` |
| Pendientes y decisiones abiertas | `PENDIENTES.md` |

Dependencias (en la PC de Ramses están todas; probado el 16/09/2026 desde una carpeta limpia):
- **Siempre:** Python 3 con Pillow y numpy.
- **MP4:** `ffmpeg` en el PATH, o `pip install imageio-ffmpeg`. Sin ninguno, se
  avisa y salen los demás formatos.
- **Verificar los SVG:** `cairosvg`. Si falta, se avisa y no se verifica.
- **Labels:** Cascadia Mono y Segoe UI Symbol de Windows, o las de `assets/fuentes/`
  (OFL, con sus licencias). Se usan solas.
- **Replicar desde código (solo Claude Code):** Node, Chrome y `puppeteer-core`,
  que vive en `scripts/node_modules`. Si falta, `npm install` dentro de `scripts/`.

En Windows el comando es `python`; en claude.ai, `python3`.

## Formatos

El motor escribe todos en cada corrida: WebP, GIF (crema y transparente), MP4,
hoja de sprites + CSS, bloque HTML, y PNG/SVG por pose. La tabla de qué usar
para cada destino está en `clawd-biblioteca`. Dos datos del motor:

- **Tiempos:** se redondean de forma acumulada. El GIF, que solo admite
  centésimas, alterna 120 y 130 ms para que 125 ms dé 1 s exacto por cada 8
  cuadros.
- **Hoja de sprites:** si pasa de 16 384 px de ancho, se parte en filas y el CSS
  usa las dos coordenadas.

## Reglas que no son de gusto

1. **Nunca sobre fondo naranja.** Clawd es naranja y desaparece.
2. **No mezclar dibujos distintos** en una pieza: canónico, el de los paseos (brazos
   de 20U) y `clawd-base` de la skill de marca.
3. **No va en piezas fijas.** En un flyer o PDF se congela: ahí va un Clawd
   quieto de `anthro-pic-brand`.

**Qué NO vive aquí.** Los Clawd sueltos (base, café, audífonos, lupa, patineta)
viven en `anthro-pic-brand/assets/clawd/`, igual que la paleta general, la
tipografía y la composición. Las animaciones terminadas viven en
`clawd-biblioteca`. `vectorizar_pixelart.py` está copiado en la skill de marca
porque las dos lo usan.
