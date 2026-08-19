# 1. Fundamento teórico y matemático

Este documento desarrolla la física y el procesamiento de señales que sustentan cada número que la aplicación reporta. La referencia normativa es **ISO 3382-1:2009**.

---

## 1.1 El recinto como sistema LTI

El auditorio se modela como un sistema **lineal e invariante en el tiempo** (LTI). Bajo ese supuesto, la relación entre una fuente y un receptor queda completamente descrita por la **respuesta al impulso** $h(t)$: la presión sonora que registra el micrófono cuando la fuente emite una delta de Dirac $\delta(t)$.

La señal percibida en la butaca es entonces la convolución

$$y(t) = (x * h)(t) = \int_{-\infty}^{\infty} x(\tau)\, h(t-\tau)\, d\tau$$

donde $x(t)$ es la señal anecoica. **Esta es exactamente la operación que ejecuta `room_sim.simulate()`** y la razón por la que el botón "escuchar con acústica del auditorio" es acústicamente correcto y no un efecto de reverberación arbitrario.

La RIR contiene tres regiones perceptualmente distintas:

| Región | Ventana típica | Origen | Efecto perceptual |
|---|---|---|---|
| Sonido directo | $t = r/c$ | trayecto recto fuente→receptor | localización, nivel |
| Reflexiones tempranas | 0 – 80 ms | 1–3 rebotes especulares | claridad, amplitud aparente de la fuente |
| Cola reverberante | > 80 ms | campo difuso estocástico | reverberación, envolvimiento |

El motor híbrido de `pyroomacoustics` refleja esta partición: el **Método de Fuentes Imagen** resuelve las dos primeras con exactitud geométrica y el **trazado de rayos** reconstruye la tercera estadísticamente.

### El Método de Fuentes Imagen (ISM)

Para una superficie plana, la reflexión especular equivale a una fuente virtual situada en la posición espejo respecto al plano. En un paralelepípedo, el conjunto de fuentes imagen de orden $\le N$ forma una retícula tridimensional. El número de fuentes crece como $O(N^3)$: pasar de orden 3 a orden 10 multiplica el costo por más de 30. De ahí que `max_order` sea el control con mayor impacto sobre el tiempo de respuesta de la aplicación.

Cada fuente imagen de orden $n$ aporta una contribución atenuada por:

- la ley del cuadrado inverso según la distancia recorrida,
- el factor de reflexión $\sqrt{1-\alpha}$ elevado al número de rebotes,
- la absorción del aire, dependiente de frecuencia, temperatura y humedad.

---

## 1.2 Filtrado en bandas de octava

ISO 3382-1 exige evaluar los parámetros **por banda**, no sobre el espectro completo, porque la absorción de los materiales y la percepción auditiva dependen fuertemente de la frecuencia.

Para una frecuencia central $f_c$, la banda de octava se define por

$$f_l = \frac{f_c}{\sqrt{2}}, \qquad f_u = f_c\sqrt{2}$$

lo que da un ancho de banda $B = f_u - f_l = f_c/\sqrt{2} \approx 0.707\, f_c$.

La implementación usa un **Butterworth de orden 4** aplicado con `scipy.signal.filtfilt`:

```python
def _filtro_octava(data, fc):
    _fl, _fu = fc / np.sqrt(2), fc * np.sqrt(2)
    _b, _a = signal.butter(4, [_fl/(fs/2), min(_fu/(fs/2), 0.99)], btype='bandpass')
    return signal.filtfilt(_b, _a, data)
```

Dos decisiones de diseño merecen atención:

- **`filtfilt` en vez de `lfilter`.** Filtra hacia adelante y hacia atrás, produciendo fase cero. Esto importa porque un desfase del filtro desplazaría el inicio aparente de la respuesta y sesgaría las ventanas de 50 y 80 ms de D50/C80. El precio es que el orden efectivo se duplica (8 en lugar de 4) y que el filtro es no causal — aceptable en post-proceso, imposible en tiempo real.
- **`min(_fu/(fs/2), 0.99)`.** Protege contra la banda de 4 kHz cuando la frecuencia de muestreo es baja: si $f_u$ superara Nyquist, `butter` fallaría. Con $f_s = 44.1$ kHz no se activa, pero blinda el código ante archivos de 16 kHz.

---

## 1.3 Integración de Schroeder

Evaluar el decaimiento directamente sobre $h^2(t)$ da una curva muy ruidosa: la cola reverberante es un proceso estocástico y ajustar una recta sobre ella tendría enorme varianza. Schroeder (1965) demostró que la **integración inversa** de la respuesta al impulso entrega, en una sola medición, la curva de decaimiento promedio que se obtendría promediando infinitas excitaciones con ruido:

$$EDC(t) = \int_{t}^{\infty} h^{2}(\tau)\, d\tau$$

En tiempo discreto esto es una suma acumulada invertida:

```python
_sq  = _rir_filt ** 2
_edc = np.cumsum(_sq[::-1])[::-1]
```

Normalizada y en decibelios:

$$EDC_{dB}(t) = 10\log_{10}\left(\frac{EDC(t)}{EDC(0)}\right)$$

El término `+ 1e-10` en el código evita $\log_{10}(0)$ al final de la señal, donde la energía remanente se anula numéricamente.

> **Implicación:** la curva EDC es monótonamente decreciente por construcción. Cualquier "meseta" al final indica que se alcanzó el piso de ruido numérico o la longitud finita de la RIR, no un fenómeno físico.

---

## 1.4 Tiempos de reverberación

El $RT_{60}$ clásico es el tiempo que tarda la energía en caer 60 dB tras apagar la fuente. En la práctica, alcanzar 60 dB limpios requiere una relación señal-ruido superior a 60 dB, difícil de lograr. La norma resuelve el problema **midiendo la pendiente en un tramo más corto y extrapolando**:

| Parámetro | Tramo de ajuste | Interpretación |
|---|---|---|
| **EDT** | 0 dB a −10 dB | Correlaciona con la reverberación *percibida*; muy sensible a las reflexiones tempranas y a la posición del receptor |
| **T20** | −5 dB a −25 dB | Estimador robusto con SNR moderada |
| **T30** | −5 dB a −35 dB | Estimador más estable del $RT_{60}$ clásico; requiere mejor SNR |

Todos arrancan en −5 dB salvo el EDT, para excluir el sonido directo y las primeras reflexiones fuertes que distorsionarían la pendiente del campo difuso.

La implementación ajusta una recta y extrapola:

```python
def _calc_tiempo(curva, u_in, u_fin):
    try:
        _i_in, _i_fin = np.where(curva <= u_in)[0][0], np.where(curva <= u_fin)[0][0]
        _m, _ = np.polyfit(np.arange(_i_in, _i_fin)/fs, curva[_i_in:_i_fin], 1)
        return -60.0 / _m
    except IndexError:
        return np.nan
```

La pendiente $m$ viene en dB/s y siempre es negativa, de modo que $T = -60/m$ es positivo. El `except IndexError` es clave: si la curva nunca cruza el umbral solicitado (por ejemplo, un decaimiento que no llega a −35 dB en una sala muy absorbente y una RIR corta), la función devuelve `NaN` en lugar de fallar. Por eso el promedio final usa `np.nanmean`.

### Relación diagnóstica EDT vs T20/T30

- $EDT \approx T20 \approx T30$: campo difuso bien desarrollado, decaimiento aproximadamente exponencial simple.
- $EDT < T20$: el decaimiento inicial es más rápido; suele indicar fuerte absorción local o predominio del sonido directo cerca de la fuente.
- $EDT > T20$: reflexiones tempranas intensas; percepción de mayor reverberación que la que sugiere el $RT_{60}$.

---

## 1.5 Parámetros de energía temprana y tardía

La inteligibilidad no depende de la energía total sino de su **distribución temporal**. El oído integra como "útil" la energía que llega dentro de una ventana de aproximadamente 50 ms para palabra y 80 ms para música (efecto de precedencia).

**Definición D50** — porcentaje de energía útil para palabra:

$$D_{50} = \frac{\int_{0}^{0.05} h^{2}(t)\,dt}{\int_{0}^{\infty} h^{2}(t)\,dt} \times 100\%$$

**Claridad C50 y C80** — razón logarítmica entre energía temprana y tardía:

$$C_{50} = 10\log_{10}\frac{\int_{0}^{0.05} h^{2}\,dt}{\int_{0.05}^{\infty} h^{2}\,dt}, \qquad C_{80} = 10\log_{10}\frac{\int_{0}^{0.08} h^{2}\,dt}{\int_{0.08}^{\infty} h^{2}\,dt}$$

En código, las ventanas se traducen a índices de muestra:

```python
_e50_t, _e50_l = np.sum(_sq[:int(0.05*fs)]), np.sum(_sq[int(0.05*fs):])
_e80_t, _e80_l = np.sum(_sq[:int(0.08*fs)]), np.sum(_sq[int(0.08*fs):])
```

Con $f_s = 44.1$ kHz, 50 ms equivalen a 2205 muestras: resolución temporal más que suficiente.

> ⚠️ **La implementación tiene un fallo aquí.** El índice 0 de la RIR es el instante de *emisión*, no el de llegada del sonido directo. ISO 3382-1 define las ventanas desde la llegada del directo, de modo que el código contabiliza el retardo de propagación como energía tardía. Ver [`05-limitaciones.md`](05-limitaciones.md) §5.2.

$C_{50}$ y $D_{50}$ contienen la misma información y se relacionan por

$$C_{50} = 10\log_{10}\left(\frac{D_{50}}{1 - D_{50}}\right)$$

con $D_{50}$ expresado como fracción. Se reportan ambos porque la literatura de inteligibilidad prefiere $D_{50}$ y la de diseño de salas prefiere $C_{50}$.

**Valores de referencia orientativos** (no normativos, dependen del uso previsto):

| Parámetro | Palabra | Música sinfónica |
|---|---|---|
| $C_{80}$ | — | −2 a +2 dB |
| $C_{50}$ | > +2 dB | — |
| $D_{50}$ | > 50 % | — |

---

## 1.6 Nivel de presión sonora absoluto

EDT, T20, C80 y D50 son **relativos**: no cambian si se sube el volumen de la fuente. Para saber cuántos decibelios recibe realmente un espectador hace falta modelar el campo sonoro completo.

En un recinto cerrado la energía tiene dos contribuciones:

- **Campo directo**, que decae con el cuadrado de la distancia,
- **Campo reverberante**, aproximadamente uniforme en toda la sala.

La **constante de sala** cuantifica la capacidad de absorción total:

$$R = \frac{S\alpha}{1-\alpha}$$

donde $S$ es la superficie total interior. En el código:

```python
_S = 2 * (ancho*largo + ancho*alto + largo*alto)
_R_sala = (_S * _alpha) / (1 - _alpha) if _alpha < 0.99 else float('inf')
```

El caso $\alpha \to 1$ se protege explícitamente: una sala totalmente absorbente tiene $R \to \infty$ y el término reverberante se anula, quedando solo campo libre.

Combinando ambos campos con el factor de directividad $Q$ ($Q = 1$ para fuente omnidireccional):

$$L_p = L_W + 10\log_{10}\left(\frac{Q}{4\pi r^{2}} + \frac{4}{R}\right)$$

La **distancia crítica** $r_c = \sqrt{QR/16\pi}$ marca el punto donde ambos campos se igualan. Más allá de $r_c$, alejarse de la fuente ya casi no reduce el nivel: es la razón física por la que en una sala reverberante las últimas filas no oyen mucho más bajo, pero sí mucho menos claro.

En la aplicación, $L_p$ se usa para **desplazar verticalmente** la curva EDC, de modo que el eje vertical de la gráfica representa presión sonora absoluta y no un decaimiento normalizado a 0 dB.

---

## Referencias

1. ISO 3382-1:2009. *Acoustics — Measurement of room acoustic parameters — Part 1: Performance spaces*.
2. Schroeder, M. R. (1965). New Method of Measuring Reverberation Time. *JASA*, 37(3), 409–412.
3. Allen, J. B., & Berkley, D. A. (1979). Image method for efficiently simulating small-room acoustics. *JASA*, 65(4), 943–950.
4. Kuttruff, H. (2016). *Room Acoustics* (6ª ed.). CRC Press.
5. Beranek, L. (2004). *Concert Halls and Opera Houses: Music, Acoustics, and Architecture* (2ª ed.). Springer.
6. Scheibler, R., Bezzam, E., & Dokmanić, I. (2018). Pyroomacoustics. *IEEE ICASSP*.
