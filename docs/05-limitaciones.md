# 5. Limitaciones, supuestos y validación

Toda simulación es un modelo con supuestos explícitos. Este documento los declara para que los resultados se interpreten con el escepticismo adecuado — especialmente si se usan como evidencia en un informe académico.

---

## 5.1 Limitaciones del modelo físico

### Absorción independiente de la frecuencia

`pra.Material(alpha)` asigna un único coeficiente a todas las bandas. En consecuencia, las diferencias entre las curvas EDC de 125 Hz y 4 kHz provienen casi solo de la absorción del aire.

**Impacto:** medio-alto. Una sala real tiene $\alpha$ marcadamente dependiente de la frecuencia: las butacas y la alfombra absorben mucho en agudos y poco en graves, lo que típicamente produce tiempos de reverberación más largos en baja frecuencia. La simulación no reproduce esa curvatura.

**Mitigación:** sustituir por materiales por banda:

```python
mat = pra.Material({
    'coeffs':       [0.15, 0.25, 0.40, 0.50, 0.55, 0.60],
    'center_freqs': [125, 250, 500, 1000, 2000, 4000],
})
```

### Reflexión puramente especular

El ISM asume superficies planas y reflexión especular. No modela difusión superficial, difracción en bordes, palcos, ni el efecto de asiento (*seat-dip*), una atenuación característica alrededor de 100–200 Hz por incidencia rasante sobre las filas de butacas.

**Impacto:** medio. Afecta sobre todo a la textura de las reflexiones tempranas y, por tanto, a $C_{80}$ y $D_{50}$.

### Geometría de caja rectangular

`ShoeBox` solo admite paralelepípedos. Un auditorio real tiene escenario, techo inclinado, balcones y paredes no paralelas — precisamente los elementos que se diseñan para evitar ecos flotantes y distribuir reflexiones.

**Impacto:** medio-alto en salas de geometría compleja. La alternativa es `pra.Room.from_corners` con extrusión, a costa de mayor tiempo de cómputo.

### Fuente omnidireccional

Se asume $Q = 1$. Una voz humana o un instrumento radian con directividad marcada, especialmente en agudos.

**Impacto:** bajo para parámetros promediados; medio para $L_p$ en receptores fuera del eje.

### Sin público

La simulación representa la sala vacía. El público es el absorbente dominante en un auditorio ocupado y puede reducir el $T_{60}$ entre 20 % y 40 %.

**Mitigación:** subir $\alpha$ para representar la condición ocupada, y declarar explícitamente cuál de las dos condiciones se está reportando.

---

## 5.2 Limitaciones de implementación

### 🐛 Las ventanas de 50 y 80 ms no descuentan el retardo de propagación — CRÍTICO

**Verificado ejecutando el cuaderno.** Es el fallo más grave del código y invalida D50, C50 y C80 tal como se calculan hoy.

ISO 3382-1 define el origen temporal de las ventanas de integración en **la llegada del sonido directo**, no en el instante de emisión. La RIR que entrega `pyroomacoustics` empieza en $t = 0$ *absoluto*, de modo que sus primeras muestras son el silencio que dura el trayecto fuente→receptor. El código integra desde el índice 0:

```python
_e50_t, _e50_l = np.sum(_sq[:int(0.05*fs)]), np.sum(_sq[int(0.05*fs):])
```

Con la configuración por defecto (18 × 30 × 7.5 m, $\alpha = 0.5$, 1 kHz), el retardo consume la ventana entera en las butacas lejanas:

| Receptor | $r$ (m) | Llegada directa | D50 código | **D50 correcto** | C80 código | **C80 correcto** |
|---|---|---|---|---|---|---|
| 0 | 7.8 | 22.8 ms | 71.4 % | 80.1 % | 7.31 dB | 8.70 dB |
| 1 | 9.4 | 27.5 ms | 63.3 % | 72.4 % | 4.98 dB | 7.02 dB |
| **2 (central)** | 14.0 | 40.8 ms | **30.0 %** | **65.2 %** | **1.29 dB** | **6.08 dB** |
| 3 | 21.4 | 62.3 ms | **0.0 %** | 62.6 % | **−7.14 dB** | 7.41 dB |
| 4 | 22.4 | 65.2 ms | **0.0 %** | 82.2 % | **−8.22 dB** | 9.20 dB |

Los receptores 3 y 4 están a más de 17 m, la distancia que el sonido recorre en 50 ms. **Su ventana "temprana" es silencio puro**, así que D50 sale exactamente 0 % y C50 alrededor de −90 dB. El promedio con `nanmean` no lo detecta —no hay `NaN`, solo ceros legítimos— y arrastra el resultado de toda la sala.

**Cómo detectarlo sin mirar el código.** D50 y C50 deben cumplir

$$C_{50} = 10\log_{10}\frac{D_{50}}{1 - D_{50}}$$

Con los valores por defecto el cuaderno reporta $D_{50} = 33\,\%$ y $C_{50} = -38.7$ dB, cuando ese $D_{50}$ implica $C_{50} = -3.1$ dB. **Una discrepancia de 35 dB entre dos parámetros que miden lo mismo** es la señal inequívoca del problema.

**Corrección:**

```python
# Origen temporal en la llegada del sonido directo
_i0 = int(np.argmax(np.abs(room_sim.rir[_i][0])))
_sq = _sq[_i0:]
# ...y a partir de aquí las ventanas de 50 y 80 ms ya son correctas
```

**Salvedad sobre `argmax`.** Tomar el máximo como origen es una aproximación, la misma que se discute en el repositorio de espectrofotometría. Falla cuando una reflexión supera al sonido directo: en el receptor 4 el pico está en 88.9 ms mientras el directo llega a 65.2 ms. El criterio riguroso es la primera muestra que supera en 20 dB al ruido de fondo antes del pico:

```python
def inicio_directo(rir, umbral_db=-20):
    pico = int(np.argmax(np.abs(rir)))
    umbral = np.abs(rir[pico]) * 10**(umbral_db/20)
    candidatos = np.where(np.abs(rir[:pico]) > umbral)[0]
    return int(candidatos[0]) if len(candidatos) else pico
```

**Nota:** los tiempos de reverberación **no** están afectados. EDT, T20 y T30 se obtienen de la pendiente de la EDC entre umbrales relativos, y un desplazamiento del origen no altera la pendiente. El fallo es exclusivo de los parámetros de energía temprana.

### Coordenadas de butacas fijas

Los receptores están en $y = $ 10, 12 y 18 m, además de dos referidos al fondo. **Si el largo se reduce por debajo de ~19 m, el asiento central queda fuera del recinto.** `pyroomacoustics` puede lanzar una excepción o devolver resultados sin sentido físico.

**Solución recomendada:** parametrizar las posiciones como fracciones del largo:

```python
_asientos = [
    [ancho*0.25, largo*0.30, 1.2],
    [ancho*0.75, largo*0.40, 1.2],
    [ancho*0.50, largo*0.55, 1.2],   # central
    [ancho*0.25, largo*0.85, 1.2],
    [ancho*0.75, largo*0.90, 1.2],
]
```

### Rango de $L_W$ inconsistente con la documentación

La tabla incrustada en el cuaderno declara 60–140 dB, pero el widget está definido como 10–130 dB. La documentación de este repositorio refleja el **código**, que es la fuente de verdad.

### `compute_rir()` redundante

Se invoca en la celda de análisis aunque `simulate()` ya haya calculado las RIR. Es idempotente pero puede duplicar trabajo en configuraciones costosas.

### Normalización que oculta el nivel

La señal auralizada se normaliza a plena escala, de modo que la comparación auditiva entre el audio seco y el procesado es válida en timbre y claridad pero **no en sonoridad**. Para evaluar nivel hay que leer la barra de $L_p$.

### Reproducción del lado del servidor

`sounddevice` reproduce en la máquina que ejecuta el kernel. Un despliegue en marimo WASM o en un servidor remoto mostrará todas las gráficas correctamente pero será mudo. Para despliegue web habría que usar `mo.audio()` con la señal codificada en WAV en memoria.

---

## 5.3 Cómo validar la simulación

### Nivel 1 — Coherencia interna

- $T_{30}$ debe caer al aumentar $\alpha$, de forma monótona.
- $D_{50}$ y $C_{50}$ deben cumplir $C_{50} = 10\log_{10}[D_{50}/(1-D_{50})]$ con $D_{50}$ en fracción. **Es la prueba que delata el fallo de §5.2**: con el código actual difieren en decenas de dB.
- $C_{80} > C_{50}$ siempre, ya que la ventana temprana es más ancha.
- $L_p$ debe decrecer con la distancia a la fuente y saturar más allá de la distancia crítica.

### Nivel 2 — Contraste analítico

Comparar el T30 simulado con la predicción de Sabine y con la de Eyring:

$$T_{Sabine} = \frac{0.161\,V}{S\alpha}, \qquad T_{Eyring} = \frac{0.161\,V}{-S\ln(1-\alpha)}$$

Eyring es más adecuada para $\alpha > 0.3$. Discrepancias del orden del 10–20 % son normales; discrepancias de factor 2 indican un problema de configuración.

### Nivel 3 — Contraste experimental

Usar los datos medidos del repositorio complementario. Procedimiento:

1. Fijar las dimensiones reales de la sala.
2. Ajustar $\alpha$ hasta igualar el T30 medido en 1 kHz.
3. Comparar el resto de bandas y de parámetros con ese $\alpha$ fijo.
4. Documentar en qué parámetros el modelo falla y atribuir cada discrepancia a una limitación concreta de esta lista.

El paso 4 es el más valioso académicamente: un modelo que se ajusta en todo suele estar sobreajustado; un modelo que falla de forma explicable enseña más.

---

## 5.4 Incertidumbre esperable

| Parámetro | Discrepancia típica frente a medición | Comentario |
|---|---|---|
| T30 | 10 – 45 % sobre Sabine | Medido en este repositorio; la brecha crece a $\alpha$ intermedios |
| T20 | 10 – 45 % | Similar a T30 |
| EDT | 20 – 40 % | Muy sensible a la geometría local, la peor reproducida |
| C80 | 2 – 4 dB | Depende de reflexiones tempranas no modeladas |
| D50 | 10 – 20 puntos porcentuales | Igual que C80 |
| $L_p$ | 3 – 6 dB | Sensible a directividad y a $L_W$ real |

Estos márgenes son orientativos y suponen una calibración previa de $\alpha$. Sin calibración, las discrepancias pueden ser considerablemente mayores.
