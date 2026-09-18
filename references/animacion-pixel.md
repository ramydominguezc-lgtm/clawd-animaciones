# Animación pixel art — método

Cómo se saca una animación de un video, y cómo se dibuja una nueva desde cero.
El motor está en `scripts/animar_pixel.py`; el ejemplo completo, en
`scripts/clawd_caminando.py`. Este documento es el criterio, no el código.

La distinción que ordena todo: **reconstruir no es recortar**. Recortar un video
te deja el ruido de compresión, el antialiasing y la paleta desaturada del
códec. Reconstruir significa recuperar la retícula lógica del dibujo, transcribir
cada pose y volver a dibujarla en los hex reales. Cuesta una hora más y el
resultado escala infinito, se recolorea y se edita.

---

# Parte A — Sacar una animación de un video

## 0. La regla que manda todo: medir, no suponer

Es tentador mirar el video y decir "el personaje camina hacia la derecha". En el
caso de Clawd, **el personaje no se movía**: su borde izquierdo estaba clavado en
x=296 px durante los 170 fotogramas. Lo que se movía era el fondo. Si hubiera
supuesto desplazamiento, cada pose habría caído en una fase distinta de la
retícula y nada habría cuadrado.

Cada afirmación sobre la animación tiene que salir de un número. Si no lo mediste,
no lo sabes.

## 1. Inventario

```bash
ffprobe -v error -show_streams video.mp4 | grep -E 'width|height|nb_frames|r_frame_rate|duration'
```

Lo que importa: resolución, fps real y número de fotogramas. Ojo con
`avg_frame_rate` distinto de `r_frame_rate` — el video puede ir a 60 fps
nominales con contenido a 12.

## 2. Extraer todo

```bash
mkdir -p frames && ffmpeg -v error -i video.mp4 -vsync 0 frames/f%03d.png
```

`-vsync 0` es obligatorio: sin él ffmpeg duplica o tira fotogramas para cuadrar
la cadencia y se pierde el compás real.

## 3. Hoja de contactos

Antes de medir nada, mirar. Una rejilla con un fotograma de cada N contesta en
diez segundos qué elementos hay, cuáles se mueven y cuál es el sujeto. Ahí se
decide qué ignorar — en este caso, las nubes del fondo.

## 4. Encontrar el ancla

Se necesitan dos anclas, una por eje, y tienen que ser cosas que **no cambien de
forma entre poses**.

- **Horizontal**: buscar un borde que se repita en todos los fotogramas. Medir el
  bbox del sujeto por fotograma y ver qué coordenada es constante. En Clawd, el
  borde izquierdo del cuerpo en la fila de los ojos.
- **Vertical**: casi nunca sirve el sujeto, porque rebota. Sirve un elemento del
  fondo: una línea de suelo, un borde de sección. En Clawd, la línea de suelo,
  que solo bajaba con el scroll de la página.

Anclas malas y por qué: el píxel más alto del sujeto (un brazo levantado lo
cambia), el centroide (cualquier pose asimétrica lo mueve), el bbox completo
(las patas lo estiran).

## 5. Encontrar la retícula lógica

Sumar la diferencia entre columnas contiguas y quedarse con los picos:

```python
d = np.abs(np.diff(sub.astype(int), axis=1)).sum(2).sum(0)
bordes = [i for i, v in enumerate(d) if v > umbral]
```

Agrupar los picos contiguos, sacar las diferencias entre grupos y buscar el
máximo común divisor aproximado. En Clawd las diferencias fueron 28, 14, 14.5,
13.5, 28.5 → paso ≈ 14, y luego aparecieron rasgos de 7 → la unidad real era la
mitad.

**Ese es el error clásico: quedarse con la celda gruesa.** Casi todo medía 2U, así
que 2U parecía la unidad. Pero varias poses movían partes 1U, y con la retícula
gruesa esos pasos se pierden y la animación queda tiesa. La regla: **la unidad es
el rasgo más pequeño que encuentres, no el más frecuente.**

Mismo razonamiento que está escrito en `scripts/vectorizar_pixelart.py`: medir
error de color, no de silueta. Una celda demasiado grande reconstruye bien el
contorno mientras destruye el detalle interior sin que la métrica se entere.

## 6. Encontrar el compás

Diferencia entre fotogramas consecutivos, recortada al área del sujeto:

```python
d = np.abs(ms[i] - ms[i-1]).sum() / 1000
```

Los picos son los cortes. Las distancias entre cortes dan las duraciones. En
Clawd salieron bloques de 5 y de 10 fotogramas a 60 fps → **12 fps, con poses que
duran 1 o 2 tiempos**. Que las duraciones sean desiguales no es un defecto de la
medición: es el ritmo de la animación y hay que conservarlo.

## 7. Cuantizar por bloque, con la moda

No cuantizar un fotograma representativo: cuantizar **todos** los del bloque y
tomar la moda por celda.

```python
moda = Counter(g[j][i] for g in fotogramas_del_bloque).most_common(1)[0][0]
```

Esto borra el ruido de compresión sin tocar el dibujo. Los artefactos típicos —
una franja oscura de un píxel arriba de cada ojo, un borde de brazo que parpadea —
aparecen en dos o tres fotogramas y desaparecen solos. Descartar el primero y el
último del bloque, que suelen traer mezcla de la transición.

Salida: cada pose como rejilla de texto, un carácter por tinta.

## 8. Verificar antes de dibujar nada

Tres pruebas, en orden de valor:

1. **Simetría de espejo.** Si la animación tiene un ciclo hacia cada lado,
   voltear uno y comparar carácter por carácter. En Clawd coincidió exacto: eso
   validó la transcripción completa de golpe y señaló las cinco celdas que aún
   eran ruido.
2. **IoU contra el original.** Renderizar la reconstrucción a la escala y
   posición del video y medir intersección sobre unión de las máscaras. Por
   arriba de 0.96 el residuo es solo el borde antialiaseado. Clawd cerró en
   **0.973**.
3. **Comparativa lado a lado.** Una tira con original arriba y reconstrucción
   abajo. Atrapa lo que las métricas perdonan.

## 9. Redibujar con los hex reales

La captura viene desaturada. Clawd salía `#d46c4d` cuando la marca es `#d97757`.
No se usa el color medido: se usa el de la paleta.

Para las tintas secundarias hay que recuperar la **relación**, no el valor. Se
divide la sombra medida entre el cuerpo medido, canal por canal:

```
180/212 = 0.849   91/107 = 0.850   66/77 = 0.857
```

Tres canales con el mismo factor ⇒ es una multiplicación. `#d97757 × 0.85 =
#b8654a`. Si los tres factores salen distintos, no es multiplicación sino un
color propio, y entonces hay que decidirlo a criterio de marca.

---

# Parte A2 — Sacar una animación de código (SVG + GSAP, CSS, Lottie)

Si la referencia es una página web, **primero se busca el código**, antes que
el video. El código trae los dibujos exactos y los tiempos declarados: no hay
compresión, ni cadencia que adivinar, ni scroll. Caso resuelto:
`scripts/clawd_confeti.py`.

## 1. Encontrar el componente

Bajar el HTML y los chunks de JS (`/_next/static/chunks/*.js` en Next.js) y
buscar un valor que el artículo cite literal. En el confeti,
`-65,-72,-76` cayó en un solo chunk. Ahí se aísla el módulo completo. Se
guarda en la biblioteca, en `_fuentes/`.

## 2. Ejecutarlo en vez de leerlo

Un componente de React compilado no se lee a mano: se ejecuta.
`scripts/capturar_gsap.js` lo monta en Chrome con un `jsx` mínimo que crea
nodos SVG reales y **el GSAP real, en la versión de la fuente**. Luego congela
la línea de tiempo global y guarda el SVG de cada instante, ya sea con un paso
fijo o con una lista de instantes.

Conviene el GSAP real y no uno simulado: los tweens (`power2.out`, `svgOrigin`,
rotaciones, `.call()` que cambian el origen a mitad de la línea) solo salen
exactos con la librería de verdad.

Dos cuidados:
- **Separar módulos por su id.** Un chunk de Next.js trae varios componentes, y
  cortar mal esconde uno. La bandera estaba dentro del bloque de Gym.
- **Dar el ancho del escenario.** Si el componente mide su contenedor, el ancho
  cambia la animación: el paseo calcula su recorrido así. Se mide en el video
  de la fuente.

## 3. Desconfiar de la demo tanto como de un video

El código dice lo que hace, no lo que el autor quiso. En el confeti, el último
`set()` estaba en t = 0.875 s. Una línea de tiempo de GSAP dura hasta su último
evento, así que el ciclo real medía 0.875 s y el cuadro 8 nunca se veía, aunque
el artículo decía "ocho cuadros a 125 ms". Lo que decide es la intención
documentada más la simetría del dibujo, **y se deja escrito por qué**.
En Gym pasó lo mismo: la pausa final de 1.5 s nunca se veía.

## 3b. Elegir cómo transcribir según el movimiento

`scripts/transcribir_svg.py` tiene tres herramientas. Se elige por lo que hace
la fuente, no por gusto:

| La fuente… | Se transcribe | Ejemplo |
|---|---|---|
| cambia de dibujo y lo mueve poco | cuadro por cuadro, fase fija del mundo | pesas |
| rota o estira (tweens) | **geometría por pieza**: `capturar_gsap.js` con `GEOMETRIA=1` y `ANCLA`, luego `piezas_a_rejilla()` | paseo |
| mueve piezas fracciones de unidad | **por piezas**: cada pieza una vez en reposo y desplazamientos redondeados a celdas | confeti, bandera |

El error que obliga a la tercera: un cuerpo de 83.7 px mide 15.7U. Si se
transcribe cuadro por cuadro mientras se mece, sale de 15 o de 16 celdas según
el cuadro, y el personaje "respira" sin razón.

**El error que obligó a la segunda** (paseo, versión 1): rasterizar al
personaje entero y muestrear por mayoría de área, a 25 fps. Con rotaciones de 3°
a 9° salían escalones de una sola columna en cualquier parte del borde, patas
partidas, ojos en L y el cuerpo respirando entre 15 y 16 celdas. Más fotogramas
no lo arreglan. Lo que lo arregla es dejar de muestrear la imagen:
- se captura la geometría de cada pieza;
- el personaje entero se mueve en celdas enteras (`ANCLA`);
- cada pieza mantiene su tamaño en celdas;
- el cuerpo no rota: se desplaza entero. Manos y ojos se colocan sin la
  rotación del cuerpo;
- las patas se pegan justo debajo del cuerpo, con al menos 2 filas (en la demo
  se despegaban y desaparecían), y una pata inclinada se dibuja recta y corrida
  entera hacia su lado. Con escalón a media pata se veía demasiado diagonal.

Se probó primero partir cada pieza en mitades con un escalón al centro. Deformaba
el cuerpo al inclinarse y Ramses lo rechazó. Opción `agacharse_desde`: si los ojos
bajan más de un umbral, el cuerpo baja una fila (el paseo se agacha al mirar abajo).

Además se captura a 20 ms (50 fps): es lo mínimo que un GIF respeta y deja
fluidos los tweens de 0.1 s.

Los accesorios dibujados en otra retícula (confeti y tela de 5 px) se
transcriben en la suya (`u=5`) y se anclan a la pieza que los sostiene (el asta
a la mano). Si se muestrean en U, el damero hace muaré.

## 4. Transcribir con fase común y moda

Rasterizar cada dibujo en alta resolución y muestrear celda por celda con la
**moda**, no con el píxel central: las demos hechas a mano tienen rectángulos
corridos fracciones de unidad, y el centro cae justo en el borde.

La fase de la retícula (dónde empieza la celda 0) se busca minimizando el error
de color, **una sola para todos los cuadros del personaje**. Si cada cuadro
elige la suya, las patas brincan 1U entre cuadros aunque en la fuente estén
plantadas.

## 5. Espejo y verificación cruzada

Si la fuente trae cuadros volteados (`matrix(-1 0 0 1 …)` o `scale(-1,1)`), se
transcribe un lado y el otro se genera con `espejo()`. Después se compara
contra una transcripción independiente del lado volteado: donde discrepan, una
de las dos tiene ruido de fase, y la otra fase lo confirma.

## 6. Capas con `componer()`

Si hay partes que van a otro ritmo o en otra posición (personaje y confeti), se
dibujan por separado y se combinan por cuadro con
`componer(lienzo, [(pose, dx, dy), ...])`. Los retrasos de cada línea de tiempo
se vuelven desfases de índice: `(t - 1) % 8`, `(t - 6) % 8`.

## 7. IoU con y sin alinear

Se mide dos veces. **Sin alinear** detecta errores de posición. **Alineado**
(la mejor traslación de menos de 1U) mide solo la forma. Si el alineado pasa y
el desfase coincide con un corrimiento que la demo mete a propósito, la
diferencia es deliberada: se documenta, no se corrige.

---

# Parte B — Dibujar una animación nueva

## La retícula

Elegir una unidad U y dibujar todo en múltiplos de U. Rasgos que definen el
carácter (ojo, ancho de extremidad) en 2U; los pasos de animación pueden usar 1U.
El lienzo se declara en unidades, no en píxeles: la escala se aplica al exportar.

Anclar el lienzo a algo físico. En Clawd la última fila apoya en el suelo, así que
`fila_inicial` de cada pose codifica directamente la altura del personaje.

## El rebote se hace con `fila_inicial`, no redibujando

Esta es la pieza que hace que valga la pena el formato `(fila_inicial, rejilla)`.
Subir el cuerpo 1U es cambiar un número. Las poses de Clawd empiezan en la fila 3,
4 o 5 según el momento del ciclo, y el dibujo no se toca.

Ojo: si el personaje sube pero los pies siguen en el suelo, **las patas tienen que
estirarse**. En Clawd la pose alta tiene patas de 4U y la baja de 3U. Sin eso el
personaje flota y se ve como un error, no como un rebote.

## Anatomía de un ciclo de caminata

El de Clawd, que es un ciclo sólido y sirve de plantilla:

| Pose | Papel | Dura |
|---|---|---|
| `a1` | contacto — patas escalonadas, cuerpo arriba | 1–2 |
| `a2` | paso — patas rectas y largas | 1 |
| `a3` | apoyo — cuerpo abajo, patas cortas | 2 |
| `a4` | impulso — un brazo arriba, cuerpo inclinado | 2 |
| `a5` | impulso opuesto — el otro brazo arriba | 2 |

Orden: `a1 a2 a3 a4 a3 a5 a3 a1`. La pose de apoyo vuelve entre cada impulso —
es lo que da el pulso. Cinco dibujos producen ocho tiempos.

Las poses de impulso son las únicas caras de dibujar y las que cargan toda la
personalidad. Las de apoyo son casi la de reposo con las patas cambiadas.

## El espejo duplica el trabajo por cero

`espejo(pose)` voltea la rejilla. Cinco poses hacia un lado dan diez. Entre los
dos ciclos hace falta una **pose de cruce** de frente (`frente` en Clawd, con las
patas más abiertas) que justifica el cambio de dirección; sin ella el personaje
salta de un lado al otro.

## Gestos de reposo

Una animación que solo camina cansa. El parpadeo de Clawd es un tiempo de 33,
dura lo mínimo y es lo que la hace parecer viva. Regla: **ojos cerrados = más
anchos y más bajos**, nunca solo más cortos. En Clawd pasa de 2U×2U a 3U×1U.

## Ritmo

12 fps es el estándar de este lenguaje; a 24 el pixel art se ve resbaloso. Las
duraciones desiguales son la herramienta principal de expresión: aguantar la pose
de reposo cinco tiempos y pasar las de transición en uno hace la diferencia entre
un bucle mecánico y algo con intención.

## Paleta

Tres tintas bastan y son lo que manda el sistema: color, su sombra al 0.85, y el
negro de marca para el detalle. Un solo acento por pieza, igual que en todo lo
demás. Cero degradados, cero contornos, cero brillos.

## Escribirla

Un archivo de datos que importe el motor:

```python
from animar_pixel import construir, espejo, verificar

PALETA = {'#': (217, 119, 87), '%': (184, 101, 74), '@': (20, 20, 19)}
LIENZO = (28, 20)

QUIETO = (4, """
......################......
......##@@########@@##......
""")

POSES = {'quieto': QUIETO, ...}
SECUENCIA = [('quieto', 5), ('parpadeo', 1), ...]

construir('salida', POSES, SECUENCIA, PALETA,
          nombre='mi-animacion', lienzo=LIENZO, escala=16, tiempo_ms=80)
```

El motor devuelve GIF opaco, GIF transparente, WebP, MP4, hoja de sprites, PNG y
SVG por pose, CSS con keyframes, una demo y el bloque HTML autónomo.

---

# Parte C — Dónde sobrevive la animación

Terminar la animación no es terminar el trabajo. El formato correcto lo decide el
destino, y hay destinos que la matan sin avisar.

| Destino | Qué usar |
|---|---|
| Web, landing | WebP — alfa real y el archivo más ligero |
| Canvas de diseño, artifact, correo | El bloque de código con SVG en línea |
| WhatsApp, Notion | GIF sobre fondo horneado |
| Instagram, TikTok | **MP4.** No aceptan HTML ni GIF animado como post |
| PDF, PPTX, impreso | Ninguno — usa una pose fija y punto |

Dos cosas que cuesta descubrir a la mala:

**Una ruta local nunca resuelve dentro de un navegador.** Que el archivo esté en
la skill significa que la herramienta lo puede leer e incrustar, no que un
`<img src="assets/...">` vaya a pintar algo. Por eso conviene emitir siempre un
bloque autónomo con el sprite en línea: pesa poco —13 poses caben en 6 KB— y
funciona en todos lados sin depender de nada.

**Las herramientas de diseño con canvas HTML corren los keyframes nativos**, así
que la animación se ve en vivo mientras se edita y sobrevive al export de HTML y
al URL compartido. Pero se congela en PDF y PPTX. Si el destino real es una red
social, la ruta es armar la pieza como HTML y renderizarla a video con Playwright,
no confiar en la exportación de la herramienta.

---

# Trampas

**Dejar que PIL cuantice el GIF.** Mete dither y colores intermedios que en pixel
art se ven como suciedad en los bordes. Construir la paleta a mano, índice por
índice, con el 0 reservado al transparente.

**Un solo GIF.** La transparencia del GIF es binaria: sobre fondo oscuro deja
borde. Exportar las dos versiones — opaca sobre crema y transparente — y elegir
por destino. Para alfa real, WebP.

**Fusionar el SVG solo en horizontal.** Sale una tira por fila. Pinta igual, pesa
el triple y no se puede leer a mano, que es media razón para tener un SVG de
pixel art. Fusionar en los dos ejes.

**Confiar en el visor.** El `view` devuelve marcos vacíos a media sesión. Probarlo
al arranque con una imagen conocida. Si falla, las poses ya son texto:
`print(pose[1])` muestra la rejilla, y `componer()` devuelve el cuadro completo
también como texto.

**Redondear tiempos cuadro por cuadro.** El GIF guarda centésimas y el MP4,
cuadros de 1/fps. Redondear cada cuadro por separado alargaba o acortaba el
ciclo: 125 ms quedaba en 120 en el GIF, y 80 ms a 60 fps quedaba en 5 cuadros de
video, que dan 2.75 s en vez de 2.64. El motor redondea de forma acumulada: el
GIF alterna 120 y 130 ms y el MP4 reparte los cuadros, así que todos los
formatos duran lo mismo. Aun así, conviene elegir `fps_video` que divida el
tiempo: 20 ms → 50 fps, 125 ms → 24 fps.

**GIF de menos de 20 ms por cuadro.** Varios visores suben a 100 ms cualquier
cuadro más corto: la animación se arrastra. 20 ms (50 fps) es el mínimo.

**Vectorizar con un trazador de curvas.** potrace y vtracer redondean los
escalones y arruinan justo lo que hace pixel art. El SVG se emite como
rectángulos, no como trazo.

**Alturas impares en ffmpeg.** `scale=800:-2`, nunca `-1`: h264 exige altura par.

**Exportar y no volver a abrir.** Cada formato se decodifica y se revisa después de
escribirlo. Un GIF con `disposal` mal puesto arrastra fantasmas del fotograma
anterior y el archivo se ve perfecto en el listado.

---

# Checklist antes de entregar

- ¿Cada afirmación sobre la animación original sale de una medición?
- ¿La unidad es el rasgo más pequeño, no el más frecuente?
- ¿Las duraciones desiguales se conservaron?
- ¿La cuantización usó la moda del bloque, no un fotograma suelto?
- ¿Los ciclos espejo coinciden carácter por carácter?
- ¿IoU por arriba de 0.96 contra el original? Si la fuente tiene corrimientos
  de menos de 1U a propósito, ¿se midió alineado y se documentó el desfase?
- ¿Los colores son los hex de la paleta, no los medidos en la captura?
- ¿Los SVG pintan exactamente lo mismo que sus PNG? (`verificar()`)
- ¿Se abrió cada formato exportado y se revisó fotograma por fotograma?
- ¿La salida quedó en `Clawd - Biblioteca/<animacion>/`, con su `LEEME.md`,
  su comparativa y su fila en `CATALOGO.md`?
