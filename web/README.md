# Beta web — Consola Acústica

Puerto interactivo en el navegador del cuaderno marimo (`app/simulacion_acustica.py`): dos archivos HTML autocontenidos (sin backend, sin build) que reimplementan el motor de fuentes imagen en JavaScript para explorarlo sin instalar Python.

- **Consola Acústica** — [demo en vivo](https://claude.ai/code/artifact/c5ccebcb-2a9c-4011-862f-48f07056519e) · [`consola-acustica.html`](consola-acustica.html)
- **Fundamentos Acústicos** — [demo en vivo](https://claude.ai/code/artifact/bac02067-5a04-4622-8702-88da22455e01) · [`fundamentos-acusticos.html`](fundamentos-acusticos.html)

## Qué reimplementa

- Método de fuentes imagen (Allen & Berkley) para geometrías tipo shoebox, en JavaScript puro.
- Filtrado de banda de octava con `BiquadFilterNode` nativo del navegador (Web Audio API), aplicado en avance y retroceso — equivalente a `filtfilt`.
- Integración de Schroeder, regresión lineal para EDT/T20/T30, D50/C50/C80 y $L_p$ por la ley del cuadrado inverso modificada — las mismas derivaciones que [`docs/01-teoria.md`](../docs/01-teoria.md), con una figura interactiva por concepto en `fundamentos-acusticos.html`.
- Auralización por convolución en tiempo real (`ConvolverNode`), con dos fuentes sintéticas (voz/instrumento) o un archivo propio.
- Presets de tipo de recinto y material predominante, comparación A/B de dos configuraciones (curvas, métricas y audio lado a lado), y modo claro/oscuro.

## Cómo abrirlas localmente

Son archivos HTML autocontenidos — sin dependencias ni servidor:

```bash
open web/consola-acustica.html
```

(o arrástralos a cualquier navegador moderno; también sirven desde un `python -m http.server` si el navegador restringe `file://`).

## Diferencias respecto al cuaderno marimo

- **No incluye** la cola estocástica de trazado de rayos ni la absorción del aire dependiente de la frecuencia que sí modela `pyroomacoustics` — captura la parte determinista (reflexiones especulares) del método de fuentes imagen. Las tendencias con volumen, absorción y orden de reflexión son físicamente correctas; los valores absolutos pueden diferir levemente del cuaderno original o de mediciones in situ.
- **D50/C50/C80** parten de la misma simplificación del cuaderno original documentada en [`docs/05-limitaciones.md`](../docs/05-limitaciones.md) §5.2 (la ventana se integra desde el instante de emisión, no desde la llegada del sonido directo, así que un receptor lejano puede tener energía temprana casi nula). Aquí ese caso se acota a un rango informativo en vez de dejar que dispare un valor sin sentido físico — sigue siendo la misma limitación de fondo, no una corrección.
- Geometría y absorción se ajustan por sliders o por los presets de recinto/material; no depende de `sounddevice` ni de un entorno Python.

## Estado

Prototipo funcional, aún no contrastado contra `analisis-acustico-centro-de-las-artes` ni contra el TFG de referencia — ver la nota de "Validación pendiente" en el pie de cada página.
