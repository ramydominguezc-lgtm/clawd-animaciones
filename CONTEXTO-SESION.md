# Contexto para trabajar estas skills en otra sesión

Lo que **no** se deduce leyendo los archivos. Los pendientes viven en
`PENDIENTES.md`, no aquí.

## Dónde está

| Skill | Carpeta | Instalada como |
|---|---|---|
| `clawd-animaciones` (genera) | `C:\Users\alfav\OneDrive\Desktop\Animaciones - Clawd` | unión en `~/.claude/skills/clawd-animaciones` |
| `clawd-biblioteca` (guarda y entrega) | `C:\Users\alfav\OneDrive\Desktop\Clawd - Biblioteca` | unión en `~/.claude/skills/clawd-biblioteca` |
| `anthro-pic-brand` (marca, hermana) | `C:\Users\alfav\OneDrive\Desktop\anthro-pic-brand` | unión |

Se recomienda Claude Code en la terminal, pero las dos skills también corren en
**claude.ai web** (se suben los ZIP del escritorio). Allá: las skills son de solo
lectura (lo nuevo sale para descargar), `python3`, fuentes de `assets/fuentes/`
en vez de las de Windows, MP4 solo con ffmpeg o `imageio-ffmpeg`, y **no** se
puede replicar desde código (no hay Chrome). Si se cambia algo aquí, hay que
volver a generar y subir los ZIP.

Las uniones no copian: se edita en el Escritorio y el cambio queda vivo. Ojo con
OneDrive: si marca una carpeta como "solo en la nube", la skill desaparece hasta
que se descargue.

**Otra sesión trabaja en paralelo sobre `anthro-pic-brand`.** El 16/09 un
archivo de esta skill (`clawd_bandera.py`) desapareció justo después de
generarse y hubo que rehacerlo. Antes de dar algo por guardado, verificar que
siga ahí.

## Límites ya decididos (no volver a discutirlos)

- **¿Se coloca o se reproduce?** Si se coloca (un sticker, aunque sea pixel
  art), va a `anthro-pic-brand/assets/clawd/`. Si se reproduce (ciclo, sprites,
  GIF, video), se genera aquí y se guarda en la biblioteca.
- **La skill generadora no guarda animaciones terminadas.** Todo va a la
  biblioteca, incluida la caminata.
- **Replicar desde código antes que desde video.** Se ejecuta el GSAP real de la
  fuente; no se lee el código a mano.
- **Se replica la intención documentada, no los errores de la demo.** El
  confeti (cuadro 8) y las pesas (pausa de 1.5 s) tenían errores de GSAP.

## Datos que cuestan una sesión si se redescubren

- **Retícula canónica:** cuerpo 16U, brazos 24U, ojos y patas 2U. En las demos
  U = 16/3 px. El paseo es otro dibujo: brazos de 20U.
- **Colores:** cuerpo `#d97757`, sombra `#b8654a` (naranja × 0.85, medido), ojo
  `#141413`. `#d46c4d` (códec) y `#DD775B` (demo) no se usan.
- **El chunk de la demo trae los 4 componentes.** La bandera (módulo 4030)
  estaba escondida dentro del bloque de Gym (282808) por un corte mal hecho.
- **Escenario del paseo:** 800 unidades SVG de recorrido, medido en el video del
  artículo. La demo lo calcula con el ancho de la página.
- **La caminata se queda en 80 ms** (decidido): se puede regenerar sobre su
  carpeta; todos sus formatos duran 2.64 s.
- **El paseo no rota el cuerpo** y dibuja las patas rectas y corridas: así lo
  prefiere Ramses, antes que escalones diagonales. Al mirar abajo se agacha.
- **Los labels de carga salen del código de Claude Code**, no de capturas: el
  binario instalado (`npm root -g`/@anthropic-ai/claude-code/bin/claude.exe)
  trae el bundle en texto. Buscar `spinnerVerbs`, `q_e()` y `claudeShimmer`.
  Detalle en `references/labels-carga.md`.

## Cómo trabaja Ramses

Está en el `CLAUDE.md` global. Lo que más importa aquí:
- responde en español, con comentarios en español;
- actúa primero y avisa después, con cambios mínimos;
- **avisa ANTES si algo puede romper lo que ya funciona**;
- **cierra cada respuesta con las decisiones pendientes**, separadas por estado.
