# 2. Arquitectura del cuaderno

## 2.1 Por qué marimo y no Jupyter

marimo almacena el cuaderno como un **archivo `.py` válido**, donde cada celda es una función decorada con `@app.cell`. Esto tiene tres consecuencias que definen la arquitectura de esta aplicación:

1. **Versionable.** El diff en Git es legible; no hay JSON con salidas embebidas.
2. **Reactivo.** marimo analiza estáticamente qué variables define y consume cada celda, construye un grafo acíclico dirigido y re-ejecuta automáticamente todo lo que dependa de un valor modificado. No existe el estado inconsistente típico de Jupyter cuando se ejecutan celdas fuera de orden.
3. **Ejecutable como aplicación.** `marimo run` oculta el código y expone solo widgets y salidas.

Las firmas de las funciones documentan el grafo explícitamente. Por ejemplo:

```python
@app.cell
def _(audio_org, fs, np, pra, sd, ui_abs, ui_alto, ui_ancho, ui_largo, ui_orden):
    ...
    return btn_reproducir_simulacion, room_sim
```

Los argumentos son las dependencias; el `return` son los productos que otras celdas podrán consumir.

---

## 2.2 Mapa de celdas

| # | Rol | Consume | Produce |
|---|---|---|---|
| 1 | Importaciones | — | `mo, np, plt, pra, sd, signal, wavfile, urllib, io` |
| 2–4 | Portada, índice y marco teórico en Markdown | `mo` | — |
| 5 | Selector de estímulo | `mo` | `sonido_widget` |
| 6 | Descarga y acondicionamiento del audio; botón de audio seco | `sonido_widget`, `urllib`, `io`, `wavfile`, `np`, `sd` | `audio_org`, `fs`, `estado` |
| 7 | Indicador de estado de carga | `estado` | — |
| 8–9 | Tablas de referencia y descripción de parámetros | `mo` | — |
| 10 | Panel de control | `mo`, `get_reset` | `ui_ancho, ui_largo, ui_alto, ui_lw, ui_abs, ui_orden, ui_freq, ui_modo_grafica` |
| 11 | Estado de reinicio | `mo` | `get_reset` |
| 12 | Botón de reproducción auralizada | `btn_reproducir_simulacion` | — |
| 13 | **Motor de simulación** | audio + geometría + `pra` | `room_sim`, `btn_reproducir_simulacion` |
| 14 | **Motor de análisis** | `room_sim`, `signal`, controles | `curvas_edc_todas`, `curva_edc_central`, `res_acusticos` |
| 15 | Gráfica EDC | resultados + `plt` | figura |
| 16 | Gráfica de barras | `res_acusticos` + `plt` | figura |

Las celdas 13 y 14 concentran prácticamente todo el costo computacional.

---

## 2.3 Celda 6 — Carga robusta del estímulo

```python
try:
    respuesta = urllib.request.urlopen(url_archivo)
    audio_bytes = respuesta.read()
    fs, audio_org = wavfile.read(io.BytesIO(audio_bytes))
    audio_org = audio_org.astype(np.float32)
    if audio_org.ndim > 1:
        audio_org = audio_org.mean(axis=1)
    audio_org = audio_org / np.max(np.abs(audio_org))
    estado = mo.md("✅ *Audio cargado desde la nube exitosamente.*")
except Exception as e:
    estado = mo.md("⚠️ **Error al descargar el audio**")
    fs = 44100
    audio_org = np.zeros(fs)
```

Puntos de diseño:

- **Descarga a memoria.** No se escribe a disco; `io.BytesIO` permite que `scipy` lea el buffer como si fuera un archivo. El cuaderno queda portátil y sin efectos secundarios sobre el sistema de archivos.
- **Degradación elegante.** Ante un fallo de red se define `fs = 44100` y un vector de ceros. Sin esto, las celdas 13 y 14 lanzarían `NameError` y toda la interfaz quedaría en rojo. Con esto, la aplicación arranca, se puede explorar la geometría y solo el audio queda mudo.
- **`fs` se hereda del archivo.** Toda la cadena (filtros, ventanas de 50/80 ms, eje temporal de la EDC) usa esa misma frecuencia de muestreo, así que un estímulo a 48 kHz funciona sin cambios.

**Mejora sugerida:** capturar excepciones específicas (`urllib.error.URLError`, `ValueError`) en lugar de `Exception`, y mostrar el mensaje real en el aviso — actualmente la variable `e` se captura pero no se usa.

---

## 2.4 Celda 13 — Motor de simulación

```python
room_sim = pra.ShoeBox(
    [ancho, largo, alto], fs=fs,
    materials=pra.Material(ui_abs.value),
    max_order=ui_orden.value,
    air_absorption=True, ray_tracing=True,
    temperature=20, humidity=50,
)

_source_loc = [ancho / 2, 4.0, 1.5]
_asientos = [
    [4.0, 10.0, 1.2],
    [ancho - 4.0, 12.0, 1.2],
    [ancho / 2, 18.0, 1.2],      # índice 2 — asiento central de referencia
    [5.0, largo - 5.0, 1.2],
    [ancho - 5.0, largo - 4.0, 1.2],
]

room_sim.add_source(_source_loc, signal=audio_org)
room_sim.add_microphone_array(pra.MicrophoneArray(np.array(_asientos).T, fs))
room_sim.simulate()
```

- La fuente se sitúa a 1.5 m de altura y 4 m de la pared frontal: altura de boca de un orador de pie sobre el escenario.
- Los receptores están a 1.2 m, altura de oído de una persona sentada.
- `pra.MicrophoneArray` espera la matriz **transpuesta**: forma $3 \times M$ (coordenadas × micrófonos), de ahí el `.T`.
- **El índice 2 es el asiento central**, elegido como referencia para las curvas EDC porque está sobre el eje de simetría y a media sala.

Tras la simulación:

```python
senal_out = room_sim.mic_array.signals[2]
if np.max(np.abs(senal_out)) > 0:
    senal_out = senal_out / np.max(np.abs(senal_out))
```

La normalización se hace **después** de la convolución. Esto significa que la comparación auditiva entre el audio seco y el auralizado es válida en timbre y claridad, pero **no en nivel absoluto**: ambos se reproducen a plena escala. Para juzgar nivel hay que mirar la barra de $L_p$, no el oído.

> **Nota de rendimiento.** `simulate()` convoluciona la señal completa con cinco RIR. Con un estímulo de 10 s y `max_order = 8` la operación puede tomar decenas de segundos. Por eso el valor por defecto es 3.

---

## 2.5 Celda 14 — Motor de análisis

Ejecuta dos barridos distintos sobre `room_sim.rir`:

**Barrido A — todas las bandas, solo el asiento central.** Alimenta la gráfica EDC en modo "Todas las frecuencias":

```python
_rir_central = room_sim.rir[2][0]
for _f in [125, 250, 500, 1000, 2000, 4000]:
    _rir_filt = _filtro_octava(_rir_central, _f)
    _edc = np.cumsum((_rir_filt**2)[::-1])[::-1]
    curvas_edc_todas[_f] = 10*np.log10((_edc/_edc[0]) + 1e-10)
```

`room_sim.rir[i][j]` indexa micrófono `i`, fuente `j`. Como hay una sola fuente, `j = 0` siempre.

**Barrido B — una banda, todos los receptores.** Alimenta los parámetros promediados y la gráfica de barras. Para cada micrófono calcula EDT, T20, T30, C50, C80, D50 y $L_p$, y al final:

```python
res_acusticos = {k: np.nanmean(v) for k, v in _temp_res.items()}
```

El uso de `nanmean` es deliberado: si en un asiento el decaimiento no alcanza −35 dB, `_calc_tiempo` devuelve `NaN` y ese punto se excluye del promedio de T30 sin invalidar los demás parámetros.

**Detalle sutil:** `room_sim.compute_rir()` se llama al inicio de esta celda aunque `simulate()` en la celda 13 ya las haya calculado. Es idempotente y garantiza que las RIR existan si el orden de ejecución cambiara, pero puede duplicar trabajo. Es un candidato claro a optimización.

---

## 2.6 Convención de variables locales

Casi todas las variables internas llevan prefijo de guion bajo: `_rir_filt`, `_edc`, `_S`, `_alpha`, `_temp_res`.

En marimo esto no es solo estilo: **las variables con prefijo `_` son locales a la celda** y no entran al grafo global. Ventajas:

- Se pueden reutilizar nombres como `_i` o `_f` en varias celdas sin conflicto.
- El grafo de dependencias queda limpio: solo aparecen los productos realmente compartidos (`room_sim`, `res_acusticos`, `curvas_edc_todas`).
- Evita el error de marimo "variable definida en múltiples celdas", que en Jupyter pasaría desapercibido y produciría resultados incorrectos.

---

## 2.7 Extensión: dónde tocar el código

| Objetivo | Celda | Cambio |
|---|---|---|
| Añadir butacas | 13 | Ampliar la lista `_asientos`; el barrido B se adapta solo |
| Absorción por frecuencia | 13 | Reemplazar `pra.Material(alpha)` por un diccionario `{'coeffs': [...], 'center_freqs': [...]}` |
| Guardar la RIR a WAV | 14 | `wavfile.write("rir.wav", fs, room_sim.rir[2][0].astype(np.float32))` |
| Exportar parámetros a CSV | nueva | `pd.DataFrame(_temp_res).to_csv(...)` — requiere añadir pandas |
| Geometría no rectangular | 13 | Sustituir `ShoeBox` por `pra.Room.from_corners` + extrusión |
| Fuente directiva | 13 | Pasar `directivity=` a `add_source` y ajustar $Q$ en el cálculo de $L_p$ |
