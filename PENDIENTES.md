# Pendientes y decisiones abiertas — animaciones de Clawd

Lista viva de las dos skills (`clawd-animaciones` y `clawd-biblioteca`). Se
actualiza en cada sesión. Última revisión: **16 de septiembre de 2026**.

Tres estados: **Decisión de Ramses** (no se toca sin su visto bueno porque
rompe algo), **Bloqueado** (falta información que solo él tiene), **Listo para
hacer** (no rompe nada, solo falta tiempo).

---

## Decisión de Ramses — rompen algo que ya funciona

| # | Qué | Por qué no se ha hecho |
|---|---|---|
Nada.

## Bloqueado — falta información que solo tiene Ramses

Nada.

## Listo para hacer — no rompe nada

| # | Qué | Nota |
|---|---|---|
| 1 | **Probar en claude.ai real** | La adaptación web se probó simulando el entorno en Windows (sin ffmpeg ni fuentes de Windows). Falta subir los ZIP a claude.ai y confirmar allá qué trae el contenedor |
| 2 | **Originales de Anthropic en X** | El artículo enlaza los 4 clips originales de @claudeai. Las réplicas salieron de la demo, que es a su vez una réplica. Compararlas contra los originales exige bajar los videos de X |

## Cerrado

- ~~Adaptar a claude.ai web~~ → fuentes OFL incluidas, MP4 opcional, rutas y guía por entorno, ZIP nuevos · 16/09
- ~~Guía de uso (GUIA.md + PDF en el escritorio), revisión completa y ZIP de las dos skills~~ · 16/09
- ~~puppeteer-core solo existía en una carpeta temporal~~ → instalado en `scripts/node_modules` · 16/09
- ~~Aprobar los dos paseos y los 10 labels~~ → aprobados por Ramses · 16/09
- ~~Revisión final de los `.md` y conexión con la skill de marca~~ · 16/09
- ~~Paseo: patas que desaparecían, cuerpo que se deformaba y patas en diagonal~~ → v3 y v4 · 16/09
- ~~Labels de carga~~ → 10 predeterminados + generador propio · 16/09
- ~~Paseo: agacharse al mirar abajo~~ → v5 · 16/09
- ~~Tiempo de la caminata~~ → se queda en 80 ms; todos los formatos duran 2.64 s · 16/09
- ~~Confeti, pesas y bandera sin visto bueno~~ → aprobadas · 16/09
- ~~Paseo con errores~~ → rehecho por piezas, 50 fps · 16/09
- ~~Tamaño del paseo para redes~~ → recorrido recortado a 2 anchos, 1008×544 px · 16/09
- ~~Comentario "200 fps" en el CSS~~ → ahora dice "Tiempo base: N ms" (CSS y demo) · 16/09
- ~~Bandera a medias~~ → borrada y rehecha desde el código de la demo · 16/09
- ~~Replicar las animaciones de la página de Codrops~~ → confeti, paseo, pesas, bandera · 16/09
- ~~Caminata dentro de la skill generadora~~ → movida a la biblioteca · 16/09
- ~~Instalar y enlazar las skills~~ → uniones en `~/.claude/skills` · 16/09
- ~~CSS y demo con acentos rotos en Windows~~ · 16/09
- ~~Bloque HTML que el motor no generaba~~ · 16/09
