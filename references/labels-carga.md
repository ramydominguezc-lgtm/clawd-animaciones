# Labels de carga — especificación

Cómo se comporta el indicador de carga de Claude Code, leído de su código
(`@anthropic-ai/claude-code` 2.1.274, `bin/claude.exe`, texto del bundle). Es la
fuente de `scripts/label_carga.py`. Si Claude Code cambia, se vuelve a leer
de ahí, no de capturas.

## Estrella

```js
var ot=["·","✢","✳","✶","✻","✻"], Lt=["·","✢","✳","✶","✻","✽"], at=["·","✢","*","✶","✻","✽"]
Cr=[...at,...at.toReversed()]            // ida y vuelta: 12 cuadros
function q_e(){ if (TERM==="xterm-ghostty") return Ar; return Cr }
zc = Math.floor(t/120) % cuadros.length  // 120 ms por cuadro
```

- En Ghostty el tercer cuadro es `✳`. En las demás terminales es un `*`
  normal. El script usa `✳`: el `*` de una letra de texto va alto y chico, y
  la estrella parece brincar.
- La estrella va en una caja de 2 celdas de ancho (`width:2`).

## Brillo

```js
le = mode==="requesting" ? 50 : 200                 // ms por paso
Ht = largo + 20                                     // pasos por vuelta
ue = mode==="requesting" ? Pt%Ht - 10 : largo + 10 - Pt%Ht
color = (i===ue || |i-ue|===1) ? shimmerColor : messageColor
```

- Tres letras a la vez (la del índice y sus vecinas).
- `requesting` (esperando respuesta): de izquierda a derecha, cada 50 ms.
- El resto (pensando, usando herramientas): de derecha a izquierda, cada 200 ms.
- Con `prefers-reduced-motion` no hay brillo ni estrella animada: sale un `●`
  fijo. El script no lo replica.

## Colores (tema de Claude Code)

| Token | Claro | Oscuro |
|---|---|---|
| `claude` (texto y estrella) | `rgb(215,119,87)` | `rgb(215,119,87)` |
| `claudeShimmer` (brillo) | `rgb(245,149,117)` | `rgb(235,159,127)` |

Hay temas ANSI y daltónicos con otros valores. El script solo hace estos dos.

## Palabras

Lista `v` del bundle: 188 verbos en gerundio, de "Accomplishing" a
"Zigzagging". "Working" es el de respaldo si no hay lista. El usuario puede
reemplazarlos o sumar los suyos con el ajuste `spinnerVerbs`. Se muestra el
verbo más `…` (U+2026).

## Decisiones del script

| Qué | Por qué |
|---|---|
| Vuelta exacta de 1440 ms (o múltiplo) | La estrella y el brillo tienen vueltas distintas. Se ajusta el paso del brillo (±10 %) para que el GIF cierre sin salto |
| Muestreo cada 20 ms | Lo mínimo que un GIF respeta en todos los visores |
| Cascadia Mono + Segoe UI Symbol | La letra por defecto de Windows Terminal no tiene los símbolos; Segoe UI Symbol los tiene todos, como la fuente de respaldo de una terminal |
| Estrella sobre la línea base del texto | Así la pinta una terminal; centrarla por su tinta la dejaba flotando |
| Una paleta por GIF | Con paleta por cuadro, el brillo parpadea |
