# Guía de uso — Animaciones de Clawd y labels de carga

Para quien va a pedir animaciones, no para quien programa el motor. Explica qué
se puede pedir, cómo pedirlo, qué se recibe y qué no se puede hacer.

---

## 1. Qué es

Dos skills que trabajan juntas, para Claude Code y claude.ai web:

| Skill | Carpeta | Qué hace |
|---|---|---|
| **`clawd-biblioteca`** | `Desktop\Clawd - Biblioteca` | **Guarda y entrega** lo que ya está hecho. No crea nada |
| **`clawd-animaciones`** | `Desktop\Animaciones - Clawd` | **Crea**: réplicas, animaciones nuevas y labels de carga |

Producen dos tipos de pieza:

- **Animaciones de Clawd en pixel art**: la mascota caminando, lanzando confeti,
  con pesas, con bandera o de paseo.
- **Labels de carga de Claude**: la estrella animada con una palabra que brilla,
  como `✻ Thinking…`.

No hace falta llamar a las skills por nombre: se le pide a Claude en lenguaje
normal ("dame el Clawd con confeti para un reel") y Claude elige cuál usar.

---

## 2. Dónde usarlas: Claude Code o claude.ai web

**Se recomienda Claude Code en la terminal** de tu computadora: ahí está todo
instalado y probado, y lo que se genera queda guardado solo en la biblioteca.
**También sirven en claude.ai web**, con algunas diferencias:

| | Claude Code (recomendado) | claude.ai web |
|---|---|---|
| Entregar lo que ya existe | Sí | Sí: te lo da para descargar |
| GIF, WebP, SVG, bloque HTML | Sí | Sí |
| MP4 | Sí | Solo si el entorno tiene ffmpeg (Claude lo revisa al empezar); si no, recibes GIF y WebP |
| Labels de carga | Sí | Sí, con fuentes incluidas en la skill: la estrella cambia apenas de trazo |
| Crear animaciones combinando poses | Sí | Sí |
| Replicar desde el código de una página | Sí | **No** (necesita Chrome) |
| Replicar desde un video | Sí | Solo si hay ffmpeg |
| Lo nuevo queda en la biblioteca | Sí, automático | **No**: se descarga. Para agregarlo hay que volver a subir el ZIP de la biblioteca, o generarlo en Claude Code |

**Cómo instalarlas**

- **Claude Code:** ya están instaladas en esta computadora. Las carpetas del
  escritorio son las skills.
- **claude.ai web:** en Configuración → Capacidades, activar la ejecución de
  código y, en Skills, subir los dos ZIP: `Clawd - Creacion (clawd-animaciones).zip`
  y `Clawd - Biblioteca (clawd-biblioteca).zip`. Si las cambias en tu
  computadora, vuelve a subir los ZIP para que la web tenga la versión nueva.

---

## 3. Lo que ya existe

Pedir algo de esta lista es inmediato y casi no gasta tokens, en Claude Code o en la web.

| Animación | Qué hace | Duración | Tamaño |
|---|---|---|---|
| `caminando` | Camina en su lugar, parpadea y se voltea | 2.64 s | 448×320 |
| `saltando` | Se agacha, salta agitando los brazos, aterriza y rebota | 1.74 s | 448×496 |
| `confeti` | Pisotea y lanza confeti con cada brazo | 1 s | 640×576 |
| `pesas` | Levanta una mancuerna, dos repeticiones | 7.1 s | 512×400 |
| `bandera` | Ondea una bandera a cuadros (bucle, o con la subida) | 0.63 s / 3.99 s | 544×496 |
| `paseo` | Mira a los lados, se agacha mirando abajo, camina y salta | 11.5 s | 1008×544 |
| `paseo-arriba` | El mismo paseo, mirando hacia arriba | 11.5 s | 1008×544 |

**Labels:** Thinking, Working, Researching, Clauding, Pondering, Cogitating,
Brewing, Noodling, Percolating, Crafting. Cada uno en tema claro y oscuro.

---

## 4. Cómo pedir

### 4.1 Pedir algo que ya existe

Basta con decir **cuál** y **para dónde**.

> "Dame el Clawd con pesas para un reel de Instagram."

> "Necesito el label Thinking en oscuro para una web."

### 4.2 Crear una animación de Clawd

Claude necesita estos datos. **Si falta uno obligatorio, pregunta; no lo inventa.**

| Dato | ¿Obligatorio? | Qué poner |
|---|---|---|
| **Modo** | Sí | `entregar` (ya existe), `replicar` (copiar una referencia) o `crear` (idea propia) |
| **Nombre** | Sí | `clawd-<acción>`, por ejemplo `clawd-saludo` |
| **Destino** | Sí | web, WhatsApp/Notion, Instagram, sitio propio, Claude Design o pose suelta |
| **Fuente** | Solo al replicar | El link o archivo de la referencia, **y** cuál animación de esa página |
| **Guion** | Solo al crear | Qué hace Clawd, paso por paso, con duraciones (ver abajo) |
| **Fondo** | No | Crema por defecto. Para oscuro o blanco se usa la versión transparente |

**Ejemplo de réplica:**

> Modo: replicar · Nombre: clawd-baile · Fuente: https://… — la animación del
> baile · Destino: reel de Instagram

**Ejemplo de creación.** El guion va en "tiempos" de 1/12 de segundo y usa poses
que ya existen:

> Modo: crear · Nombre: clawd-saludo · Destino: web  
> Guion: caminando.quieto 5 · caminando.parpadeo 1 · confeti.A1 1 · confeti.A2 2
> · confeti.A1 1 — bucle: sí

Poses disponibles para combinar:

- **caminando**: `quieto`, `parpadeo`, `frente`, `a1`–`a5` (paso hacia un lado),
  `b1`–`b5` (hacia el otro)
- **confeti**: `AGACHADO`, `A1`–`A3` (brazo derecho arriba), `B1`–`B3` (izquierdo)

Si la idea necesita una pose que no existe (por ejemplo, un Clawd sentado),
Claude la dibuja sobre la retícula de Clawd y **te muestra una hoja de contactos
para que la apruebes antes de exportar**.

### 4.3 Crear un label de carga

Solo hace falta **la palabra**. Opcionales: **modo del brillo** y **tamaño**.

> "Hazme un label que diga Investigando."

> "Label 'Diseñando', brillo lento, letra grande."

| Dato | Valores |
|---|---|
| Palabra | Cualquiera, sin los tres puntos (se agregan solos) |
| Modo | `solicitando` (brillo rápido de izquierda a derecha, por defecto) o `pensando` (lento, de derecha a izquierda) |
| Tamaño | Tamaño de letra en px. 40 por defecto (~300 px de ancho) |

---

## 5. Qué se recibe

### Animaciones de Clawd

| Para | Archivo |
|---|---|
| Instagram (post, reel, story) | `.mp4` |
| Web, landing | `.webp` (transparente) |
| WhatsApp, correo, Notion | `.gif` (fondo crema) |
| Fondo que no es crema | `-transparente.gif` |
| Claude Design, artifacts | `-bloque.html` (se pega tal cual y anima solo) |
| Sitio propio | `-hoja.png` + `.css` |
| Una pose fija | `svg/…svg` |

Cada animación trae además un `LEEME.md` con sus diferencias respecto a la
fuente y una imagen comparativa.

### Labels

`-claro.gif`, `-oscuro.gif`, `-claro.mp4`, `-oscuro.mp4`, `-claro.webp` y
`-oscuro.webp` (transparentes) y `-bloque.html` (anima en vivo; tema con
`data-tema="oscuro"`).

---

## 6. Alcances — qué sí puede hacer

- **Replicar animaciones de Clawd desde una página web**, leyendo su código (lo
  más preciso) o midiendo un video.
- **Detectar y corregir errores de la fuente.** Por ejemplo, el cuadro que la
  demo del confeti nunca mostraba.
- **Crear animaciones nuevas** combinando poses existentes o dibujando poses
  nuevas con tu aprobación.
- **Variantes de una animación** cambiando un solo movimiento, como el paseo
  mirando arriba.
- **Labels de carga con cualquier palabra**, idénticos al comportamiento real de
  Claude Code: los 6 símbolos de la estrella, el ritmo de 120 ms y el brillo de
  3 letras.
- **Todos los formatos a la vez**, con tiempos exactos en GIF, WebP y MP4.
- **Regenerar cualquier animación idéntica** a partir de su receta.

---

## 7. Limitaciones — qué no puede hacer

### De diseño (reglas que no se rompen)

- **Solo Clawd.** Otros personajes o mascotas no tienen retícula ni poses.
- **Nunca sobre fondo naranja**: Clawd es naranja y desaparece.
- **No sirve para piezas fijas** (flyer, PDF, post estático): la animación se
  congela. Ahí va un Clawd quieto de la skill de marca.
- **No se mezclan dibujos distintos** en una pieza. El Clawd del paseo tiene
  brazos más cortos que el de la caminata.
- **Colores fijos.** Clawd siempre `#d97757`. Los labels usan el color del
  producto y no se recolorean.

### Técnicas

- **Arma la animación, no el post completo.** El texto, el fondo y la
  composición del post se hacen con la skill de marca o en Claude Design, y
  después se inserta la animación.
- **Las rotaciones se simplifican.** Si la fuente gira el cuerpo, en pixel art el
  cuerpo se desplaza sin rotar: rotarlo lo deforma.
- **Replicar desde video es menos preciso** que desde código. Los videos de X o
  Instagram no traen código: se mide cuadro a cuadro y tarda más.
- **Las poses nuevas cuestan.** Dibujarlas gasta más tokens y requiere tu revisión.
- **GIF:** mínimo 20 ms por cuadro (50 fps) y transparencia sin bordes suaves.
  Para fondos oscuros conviene WebP o el GIF oscuro de los labels.
- **Labels:**
    - solo temas claro y oscuro;
    - en la estrella se usa `✳` en lugar del `*` de la mayoría de terminales;
    - el brillo se ajusta hasta ±10 % para que el bucle cierre sin salto;
    - no incluye el modo sin movimiento de Claude Code.
- **En claude.ai web hay menos herramientas.** No se puede replicar desde el
  código de una página, el MP4 depende de que haya ffmpeg y lo generado no se
  guarda solo en la biblioteca. Ver la sección 2.
- **OneDrive:** si una carpeta queda "solo en la nube", la skill deja de verse
  hasta que se descargue.

---

## 8. Cuánto cuesta cada pedido

| Pedido | Costo aproximado |
|---|---|
| Entregar algo que ya existe | Muy bajo: se lee el catálogo y se da la ruta |
| Label nuevo | Bajo: un comando, segundos |
| Animación combinando poses existentes | Medio |
| Réplica desde código de una página | Alto: extraer, capturar, transcribir, verificar |
| Réplica desde video o con poses nuevas | El más alto |

Por eso conviene **revisar primero la biblioteca** y pedir variantes de lo que
ya existe antes que animaciones desde cero.

---

## 9. Si algo falla

| Síntoma | Causa probable | Solución |
|---|---|---|
| No sale el `.mp4` | Falta ffmpeg | Instalarlo y dejarlo en el PATH |
| "SVG sin verificar (falta cairosvg)" | Falta la librería | `pip install cairosvg` |
| Falla la captura de una página | Falta puppeteer-core | `npm install` dentro de `Animaciones - Clawd\scripts` |
| Claude no encuentra la skill | OneDrive la dejó en la nube | Clic derecho en la carpeta → "Mantener siempre en este dispositivo" |
| El label sale con letra rara | Faltan Cascadia Mono o Segoe UI Symbol | Vienen con Windows 11; reinstalar si se borraron |
| En claude.ai no sale el MP4 | El entorno web no tiene ffmpeg | Pedir a Claude `pip install imageio-ffmpeg`; si no se puede, usar el GIF o generar el MP4 en Claude Code |
| En claude.ai no aparece lo que generé antes | La biblioteca web es de solo lectura | Volver a subir el ZIP de la biblioteca actualizado |
| En claude.ai no se puede replicar una página | Necesita Chrome | Hacerlo en Claude Code |

---

## 10. Dónde está cada cosa

```
Desktop\Animaciones - Clawd\          CREACIÓN (clawd-animaciones)
  SKILL.md                            instrucciones para Claude
  GUIA.md                             esta guía
  PENDIENTES.md                       decisiones abiertas
  references\animacion-pixel.md       método técnico de pixel art
  references\labels-carga.md          especificación de los labels
  scripts\                            motor, recetas y herramientas
  assetsuentes\                     fuentes libres para usar los labels en la web

Desktop\Clawd - Biblioteca\           BIBLIOTECA (clawd-biblioteca)
  SKILL.md · CATALOGO.md              qué hay y cómo entregarlo
  <animación>\                        formatos + LEEME + comparativa
  labels\                             labels de carga + muestrario
  _fuentes\                           material original de las réplicas
```
