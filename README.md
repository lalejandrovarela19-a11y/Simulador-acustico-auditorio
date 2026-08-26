# Simulador Acústico de Auditorios

**Auralización interactiva y cálculo de parámetros ISO 3382-1 mediante el Método de Fuentes Imagen.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![marimo](https://img.shields.io/badge/notebook-marimo-purple)](https://marimo.io/)
[![pyroomacoustics](https://img.shields.io/badge/engine-pyroomacoustics-orange)](https://github.com/LCAV/pyroomacoustics)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## ¿Qué hace esta aplicación?

Es un cuaderno reactivo de [marimo](https://marimo.io/) que **simula el comportamiento acústico de un auditorio rectangular** y permite:

1. **Escuchar** el mismo material sonoro (voz o saxofón) en dos versiones: seco (anecoico) y convolucionado con la respuesta al impulso del recinto simulado — es decir, *auralización*.
2. **Calcular** los parámetros acústicos objetivos de la norma **ISO 3382-1**: EDT, T20, T30, C50, C80, D50 y nivel de presión sonora absoluto $L_p$.
3. **Visualizar** la curva de decaimiento de energía (EDC) de Schroeder por banda de octava, con los umbrales normativos superpuestos.
4. **Experimentar** en tiempo real: cada vez que se modifica una dimensión, el coeficiente de absorción o el orden de reflexiones, todo el grafo de cálculo se re-ejecuta automáticamente.

La geometría por defecto (18 m × 30 m × 7.5 m) corresponde al auditorio del **Centro de las Artes del Instituto Tecnológico de Costa Rica**, lo que permite contrastar la simulación contra las mediciones experimentales del repositorio complementario [`analisis-acustico-centro-de-las-artes`](../analisis-acustico-centro-de-las-artes).

---

## Índice

- [Versión web (beta, sin instalación)](#versión-web-beta-sin-instalación)
- [Instalación y ejecución](#instalación-y-ejecución)
- [Cómo funciona: recorrido por la aplicación](#cómo-funciona-recorrido-por-la-aplicación)
- [Arquitectura del cuaderno](#arquitectura-del-cuaderno)
- [Parámetros de control](#parámetros-de-control)
- [Fundamento teórico (resumen)](#fundamento-teórico-resumen)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Documentación extendida](#documentación-extendida)
- [Cómo citar](#cómo-citar)
- [Licencia](#licencia)

---

## Versión web (beta, sin instalación)

[`web/`](web/) contiene un puerto en el navegador del mismo motor de fuentes imagen — dos archivos HTML autocontenidos (JavaScript puro, sin backend) que no requieren Python:

- **[Consola Acústica](https://claude.ai/code/artifact/c5ccebcb-2a9c-4011-862f-48f07056519e)** — la app interactiva, con presets de recinto/material, comparación A/B y auralización en el navegador.
- **[Fundamentos Acústicos](https://claude.ai/code/artifact/bac02067-5a04-4622-8702-88da22455e01)** — una figura interactiva por concepto teórico (fuentes imagen, bandas de octava, integración de Schroeder, EDT/T20/T30, D50/C50/C80, $L_p$).

Es un prototipo complementario al cuaderno marimo, no un reemplazo — ver [`web/README.md`](web/README.md) para el detalle de qué reimplementa y en qué difiere.

---

## Instalación y ejecución

### Opción A — `uv` (recomendada)

El archivo `app/simulacion_acustica.py` incluye metadatos inline **PEP 723**, así que `uv` resuelve las dependencias sin necesidad de crear un entorno manualmente:

```bash
uv run marimo edit app/simulacion_acustica.py
```

Para abrirlo en modo aplicación (sin celdas de código a la vista):

```bash
uv run marimo run app/simulacion_acustica.py
```

### Opción B — `pip` + entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
marimo edit app/simulacion_acustica.py
```

> **Nota sobre el audio.** La reproducción usa `sounddevice`, que envía la señal al dispositivo de salida **de la máquina donde corre el kernel de Python**. Esto funciona en ejecución local, pero *no* en marimo WASM ni en un servidor remoto. En Linux puede requerir PortAudio: `sudo apt install libportaudio2`.

### Requisitos del sistema

| Componente | Versión | Notas |
|---|---|---|
| Python | ≥ 3.11 | El encabezado original pide ≥ 3.14; se relajó a 3.11 por compatibilidad con `pyroomacoustics` |
| RAM | ≥ 4 GB | El trazado de rayos con `max_order ≥ 6` es intensivo |
| Salida de audio | opcional | Sin ella el cuaderno funciona, pero los botones de reproducción no suenan |

---

## Cómo funciona: recorrido por la aplicación

La aplicación se recorre de arriba hacia abajo en cinco etapas.

### 1. Selección y carga del estímulo

Un `mo.ui.dropdown` ofrece dos señales anecoicas alojadas en GitHub (voz humana y saxofón). El cuaderno las descarga a memoria con `urllib.request`, las lee con `scipy.io.wavfile` desde un `io.BytesIO` y las acondiciona:

- conversión a `float32`,
- mezcla a mono si el archivo es estéreo (`audio.mean(axis=1)`),
- normalización por el valor absoluto máximo.

Si la descarga falla, el cuaderno degrada elegantemente a un vector de silencio de 1 s y muestra un aviso, en lugar de romper toda la cadena reactiva.

El botón **🎵 1. Audio original** reproduce esta señal seca, que es la referencia perceptual contra la cual se compara la versión auralizada.

### 2. Construcción del recinto virtual

Con las dimensiones del panel de control se instancia una `pra.ShoeBox` (caja de zapatos, es decir un paralelepípedo rectangular):

```python
room_sim = pra.ShoeBox(
    [ancho, largo, alto], fs=fs,
    materials=pra.Material(alpha),
    max_order=orden,
    air_absorption=True, ray_tracing=True,
    temperature=20, humidity=50,
)
```

- **`materials=pra.Material(alpha)`** asigna un coeficiente de absorción único y uniforme a las seis superficies.
- **`max_order`** limita el orden del Método de Fuentes Imagen (ISM), que resuelve con exactitud geométrica las reflexiones tempranas.
- **`ray_tracing=True`** activa el motor híbrido: el ISM cubre las primeras reflexiones y el trazado estocástico de rayos reconstruye la cola reverberante tardía, evitando el crecimiento exponencial del número de fuentes imagen.
- **`air_absorption`, `temperature`, `humidity`** aplican la atenuación del aire dependiente de la frecuencia, dominante por encima de 2 kHz.

La fuente se coloca en el centro del escenario, a $(ancho/2,\ 4.0,\ 1.5)$ m, y se despliegan **cinco receptores** que emulan butacas. El índice `2` corresponde al asiento central y es el que se usa para todas las gráficas de EDC.

### 3. Auralización

`room_sim.simulate()` convoluciona la señal de entrada con la respuesta al impulso de cada receptor. La señal resultante en el asiento central se normaliza y queda disponible en el botón **🔊 2. Escuchar con acústica del auditorio**.

Comparar ambos botones es el núcleo pedagógico de la herramienta: con $\alpha = 0.05$ y `max_order = 8` la voz se vuelve ininteligible; con $\alpha = 0.6$ recupera nitidez a costa de "secarse".

### 4. Cálculo de parámetros

Para cada receptor y cada banda de octava ISO (125 Hz a 4 kHz):

1. Se filtra la RIR con un **Butterworth pasabanda de orden 4** ($f_l = f_c/\sqrt{2}$, $f_u = f_c\sqrt{2}$), aplicado con `filtfilt` para no introducir desfase.
2. Se eleva al cuadrado y se integra hacia atrás (**integral de Schroeder**) mediante `np.cumsum(sq[::-1])[::-1]`.
3. Se normaliza y se pasa a dB.
4. Se ajusta una recta por mínimos cuadrados (`np.polyfit`) en los tramos normativos para obtener **EDT** (0 a −10 dB), **T20** (−5 a −25 dB) y **T30** (−5 a −35 dB), extrapolando la pendiente $m$ a 60 dB: $T = -60/m$.
5. Se integran las ventanas de 50 ms y 80 ms para obtener **D50**, **C50** y **C80**.
6. Se calcula $L_p$ con la ecuación de campo directo más campo reverberante.

Los resultados se promedian entre receptores con `np.nanmean`, de forma que un punto donde el decaimiento no alcance −35 dB no contamina el promedio con `NaN`.

### 5. Visualización

Dos figuras de Matplotlib:

- **Curva EDC** desplazada al nivel absoluto $L_p$, en modo banda única o superposición de las seis bandas, con líneas de umbral en −10, −25 y −35 dB.
- **Panel de barras** con tiempos de reverberación, índices de claridad y nivel de presión sonora, anotados con su valor numérico.

---

## Arquitectura del cuaderno

marimo no ejecuta celdas en orden de escritura: construye un **grafo acíclico dirigido** a partir de las variables que cada celda define y consume. El flujo real es:

```
 [dropdown de sonido]
          │
          ▼
 [descarga + acondicionamiento]  ──►  fs, audio_org
          │                                │
          │                                ▼
 [panel de control] ──► ui_ancho, ui_largo, ui_alto,
          │              ui_abs, ui_orden, ui_lw,
          │              ui_freq, ui_modo_grafica
          │                                │
          └────────────────┬───────────────┘
                           ▼
              [pra.ShoeBox + simulate()]  ──►  room_sim, señal auralizada
                           │
                           ▼
              [compute_rir + filtrado + Schroeder]
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
        curvas_edc_todas      res_acusticos
                  │                 │
                  ▼                 ▼
           [gráfica EDC]     [gráfica de barras]
```

Consecuencia práctica: mover el deslizador de absorción invalida `room_sim`, lo que invalida las RIR, los parámetros y ambas gráficas — todo se recalcula sin intervención del usuario. Es también el motivo por el que subir `max_order` a 10 hace que la interfaz tarde varios segundos en responder.

Detalle de estilo: las variables auxiliares llevan prefijo `_` (`_rir_filt`, `_edc`, `_S`). En marimo esto las marca como **locales a la celda**, evitando colisiones de nombres entre celdas y manteniendo el grafo limpio.

---

## Parámetros de control

| Categoría | Parámetro | Rango en código | Paso | Por defecto |
|---|---|---|---|---|
| Dimensiones | Ancho | 5.0 – 30.0 m | 1.0 m | 18.0 m |
| Dimensiones | Largo | 10.0 – 50.0 m | 1.0 m | 30.0 m |
| Dimensiones | Alto | 3.0 – 15.0 m | 0.5 m | 7.5 m |
| Física | Potencia de fuente $L_W$ | 10 – 130 dB | 1 dB | 100 dB |
| Física | Coeficiente de absorción $\alpha$ | 0.05 – 0.95 | 0.05 | 0.50 |
| Motor | Orden de reflexiones (ISM) | 1 – 10 | 1 | 3 |
| Análisis | Frecuencia ISO | 125 / 250 / 500 / 1k / 2k / 4k Hz | — | 1000 Hz |
| Visualización | Modo de gráfica EDC | Única / Todas | — | Única |

Ver [`docs/04-parametros.md`](docs/04-parametros.md) para la interpretación física de cada uno y valores típicos de $\alpha$ por material.

---

## Fundamento teórico (resumen)

El recinto se modela como un sistema **lineal e invariante en el tiempo**, completamente caracterizado por su respuesta al impulso $h(t)$.

**Curva de decaimiento de energía (Schroeder):**

$$EDC(t) = \int_{t}^{\infty} h^{2}(\tau)\, d\tau, \qquad EDC_{dB}(t) = 10\log_{10}\frac{EDC(t)}{EDC(0)}$$

**Definición y claridad:**

$$D_{50} = \frac{\int_{0}^{0.05} h^{2}(t)\,dt}{\int_{0}^{\infty} h^{2}(t)\,dt} \times 100\%$$

$$C_{80} = 10\log_{10}\frac{\int_{0}^{0.08} h^{2}(t)\,dt}{\int_{0.08}^{\infty} h^{2}(t)\,dt} \ \ \text{[dB]}$$

**Nivel de presión sonora en campo mixto**, con constante de sala $R = S\alpha/(1-\alpha)$ y directividad $Q$:

$$L_p = L_W + 10\log_{10}\left(\frac{Q}{4\pi r^{2}} + \frac{4}{R}\right)$$

El desarrollo completo, incluida la justificación del filtrado en bandas de octava y de la extrapolación a 60 dB, está en [`docs/01-teoria.md`](docs/01-teoria.md).

---

## Estructura del repositorio

```
simulador-acustico-auditorio/
├── app/
│   └── simulacion_acustica.py      # Cuaderno marimo (aplicación completa)
├── assets/
│   └── README.md                   # Cómo alojar los estímulos anecoicos
├── docs/
│   ├── 01-teoria.md                # Derivaciones y normativa ISO 3382-1
│   ├── 02-arquitectura.md          # Grafo reactivo, celda por celda
│   ├── 03-guia-de-uso.md           # Recorrido guiado y experimentos sugeridos
│   ├── 04-parametros.md            # Referencia de cada control
│   └── 05-limitaciones.md          # Supuestos, sesgos y validación
├── web/
│   ├── README.md                   # Qué reimplementa la beta web y en qué difiere
│   ├── consola-acustica.html       # App interactiva (HTML/JS autocontenido)
│   └── fundamentos-acusticos.html  # Fundamentos teóricos con figuras interactivas
├── requirements.txt
├── pyproject.toml
├── CITATION.cff
├── CONTRIBUTING.md
└── LICENSE
```

---

## Limitaciones conocidas

Documentadas en detalle en [`docs/05-limitaciones.md`](docs/05-limitaciones.md). Las principales:

1. **🐛 D50, C50 y C80 están mal calculados.** Las ventanas de 50 y 80 ms se integran desde el instante de emisión, no desde la llegada del sonido directo como exige ISO 3382-1. En las butacas a más de 17 m la ventana temprana es silencio puro y D50 sale 0 %. Verificado ejecutando el cuaderno; corrección en [`docs/05-limitaciones.md`](docs/05-limitaciones.md) §5.2. Los tiempos de reverberación no están afectados.
2. **Absorción independiente de la frecuencia.** `pra.Material(alpha)` aplica el mismo $\alpha$ a todas las bandas, de modo que las diferencias entre las curvas EDC de 125 Hz y 4 kHz provienen casi solo de la absorción del aire. Un auditorio real presenta variación espectral fuerte (butacas, alfombra, madera).
3. **Geometría de butacas fija.** Los cinco receptores usan coordenadas $y$ fijas (10, 12, 18, largo−5, largo−4). Si se reduce el largo por debajo de ~19 m, receptores quedan fuera del recinto y `pyroomacoustics` puede fallar o entregar resultados sin sentido físico.
4. **Sin difusión ni difracción.** El ISM asume reflexión especular sobre superficies planas; no modela paneles difusores, palcos ni el efecto de asiento (*seat-dip*).
5. **Reproducción del lado del servidor.** `sounddevice` no funciona en despliegues WASM ni remotos.
6. **El botón de reinicio es parcial.** Existe un estado `get_reset`/`set_reset` que actúa como disparador, pero los widgets se re-crean con sus valores por defecto solo si la celda que los define depende de ese estado; conviene verificarlo tras modificar el panel.

Ninguna de estas limitaciones invalida el uso docente y comparativo de la herramienta, pero deben declararse al contrastar la simulación contra mediciones reales.

---

## Documentación extendida

| Documento | Contenido |
|---|---|
| [`docs/01-teoria.md`](docs/01-teoria.md) | Sistema LTI, ISM, filtrado en octavas, integral de Schroeder, derivación de cada parámetro |
| [`docs/02-arquitectura.md`](docs/02-arquitectura.md) | Grafo reactivo, mapa de celdas, análisis del código y puntos de extensión |
| [`docs/03-guia-de-uso.md`](docs/03-guia-de-uso.md) | Recorrido guiado, cinco experimentos, lectura de gráficas, resolución de problemas |
| [`docs/04-parametros.md`](docs/04-parametros.md) | Referencia de cada control con valores típicos por material |
| [`docs/05-limitaciones.md`](docs/05-limitaciones.md) | Supuestos del modelo, errores de implementación y protocolo de validación |

---

## Cómo citar

Ver [`CITATION.cff`](CITATION.cff). Referencias normativas y de software:

- ISO 3382-1:2009. *Acoustics — Measurement of room acoustic parameters — Part 1: Performance spaces*. International Organization for Standardization.
- Scheibler, R., Bezzam, E., & Dokmanić, I. (2018). *Pyroomacoustics: A Python package for audio room simulation and array processing algorithms*. IEEE ICASSP. https://doi.org/10.1109/ICASSP.2018.8461310
- Schroeder, M. R. (1965). *New Method of Measuring Reverberation Time*. JASA, 37(3), 409–412.
- Kuttruff, H. (2016). *Room Acoustics* (6ª ed.). CRC Press.

---

## Licencia

MIT — ver [`LICENSE`](LICENSE).
# Simulador-acustico-auditorio
# Simulador-acustico-auditorio
