# 4. Referencia de parámetros

## 4.1 Dimensiones del recinto

| Control | Rango | Paso | Defecto |
|---|---|---|---|
| Ancho | 5.0 – 30.0 m | 1.0 m | 18.0 m |
| Largo | 10.0 – 50.0 m | 1.0 m | 30.0 m |
| Alto | 3.0 – 15.0 m | 0.5 m | 7.5 m |

Definen el volumen $V$ y la superficie $S$, que gobiernan el tiempo de reverberación por la relación de Sabine:

$$T_{60} \approx \frac{0.161\,V}{S\alpha}$$

Los valores por defecto corresponden al auditorio del Centro de las Artes del TEC: $V = 4050$ m³, $S = 1800$ m².

**Advertencia:** los receptores usan coordenadas $y$ fijas (10, 12 y 18 m). Con un largo inferior a ~19 m, el asiento central queda fuera del recinto. Mantenga el largo por encima de 20 m salvo que modifique la lista `_asientos`.

## 4.2 Nivel de potencia sonora $L_W$

Rango 10 – 130 dB, defecto 100 dB. Es la potencia acústica total radiada por la fuente, independiente de la sala.

| Fuente | $L_W$ orientativo |
|---|---|
| Voz susurrada | 30 – 40 dB |
| Voz conversacional | 60 – 70 dB |
| Voz proyectada de orador | 75 – 85 dB |
| Instrumento acústico solista | 85 – 100 dB |
| Sistema de refuerzo sonoro | 110 – 130 dB |

Solo afecta $L_p$; desplaza la curva EDC verticalmente sin cambiar su pendiente, de modo que EDT, T20, T30, C50, C80 y D50 permanecen idénticos. Es la manifestación práctica de que los parámetros ISO 3382-1 son independientes del nivel.

## 4.3 Coeficiente de absorción $\alpha$

Rango 0.05 – 0.95, paso 0.05, defecto 0.50. Fracción de energía absorbida en cada reflexión: $\alpha = 0$ es reflexión perfecta, $\alpha = 1$ absorción total.

| Material | $\alpha$ típico a 1 kHz |
|---|---|
| Concreto pulido, vidrio, mármol | 0.02 – 0.05 |
| Yeso sobre mampostería | 0.05 – 0.10 |
| Madera contrachapada sobre cámara | 0.10 – 0.20 |
| Alfombra sobre contrapiso | 0.25 – 0.40 |
| Butacas tapizadas vacías | 0.40 – 0.60 |
| Público sentado | 0.70 – 0.85 |
| Panel acústico poroso de 50 mm | 0.80 – 0.95 |

Se aplica un valor **único y uniforme** a las seis superficies y a todas las bandas. Para modelar una sala real hay que usar un promedio ponderado por área:

$$\alpha_{eq} = \frac{\sum_i S_i \alpha_i}{\sum_i S_i}$$

## 4.4 Orden de reflexiones (ISM)

Rango 1 – 10, defecto 3. Número máximo de rebotes que traza el Método de Fuentes Imagen.

| Orden | Fuentes imagen (aprox.) | Uso |
|---|---|---|
| 1 – 2 | decenas | Exploración rápida; cola reverberante pobre |
| 3 – 5 | cientos | Equilibrio recomendado |
| 6 – 8 | miles | Alta fidelidad; segundos a decenas de segundos |
| 9 – 10 | decenas de miles | Solo para validación puntual |

El crecimiento es cúbico en el orden. Como el trazado de rayos está activado, la cola tardía se reconstruye estadísticamente incluso con órdenes bajos: por eso órdenes moderados dan resultados aceptables. Los parámetros de claridad ($C_{50}$, $C_{80}$, $D_{50}$) son los más sensibles al orden, porque dependen de resolver bien las reflexiones tempranas.

## 4.5 Frecuencia ISO de análisis

Opciones: 125, 250, 500, 1000, 2000 y 4000 Hz. Defecto 1000 Hz.

Selecciona la banda de octava sobre la que se calculan todos los parámetros del panel de barras. Por convención, los valores "de sala" se reportan como promedio de 500 Hz y 1 kHz, las bandas donde la audición humana es más sensible y donde se concentra la energía de la voz.

La banda de 63 Hz no se incluye porque a esa frecuencia el comportamiento es modal, no difuso, y los métodos geométricos pierden validez. El límite inferior de validez del ISM se estima con la frecuencia de Schroeder:

$$f_s \approx 2000\sqrt{\frac{T_{60}}{V}}$$

Para la sala por defecto con $T_{60} \approx 0.7$ s, resulta $f_s \approx 26$ Hz, bastante por debajo de 125 Hz: el modelo geométrico es aplicable en todo el rango analizado.

## 4.6 Modo de gráfica EDC

- **"Solo la seleccionada":** una curva, con umbrales normativos visibles. Para análisis detallado de una banda.
- **"Todas las frecuencias":** las seis bandas superpuestas con colores distintos. Para detectar coloración espectral, es decir, bandas que decaen a ritmos marcadamente distintos.

## 4.7 Botón de reinicio

Incrementa un estado interno (`get_reset` / `set_reset`) del que depende la celda del panel de control, forzando su re-ejecución y con ella la recreación de los widgets con sus valores por defecto. Conviene verificar su comportamiento tras cualquier modificación al panel, ya que solo funciona mientras esa dependencia se mantenga.
