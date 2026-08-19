# 3. Guía de uso

## 3.1 Primer recorrido (5 minutos)

1. **Ejecute** `uv run marimo edit app/simulacion_acustica.py`. El navegador abre el cuaderno.
2. **Espere** el aviso ✅ de carga de audio. Si aparece ⚠️, revise la conexión: los estímulos se descargan de GitHub.
3. **Pulse `🎵 1. Audio original`.** Esta es la referencia anecoica.
4. **Pulse `🔊 2. Escuchar con acústica del auditorio`** con los valores por defecto (18 × 30 × 7.5 m, $\alpha = 0.5$, orden 3). La diferencia debe ser audible pero moderada.
5. **Baje el coeficiente de absorción a 0.05** y vuelva a escuchar. La voz debería volverse notablemente confusa.
6. **Observe** cómo T30 sube en la gráfica de barras y cómo la curva EDC se aplana.

---

## 3.2 Experimentos sugeridos

### A. El compromiso inteligibilidad ↔ reverberación

Fije la geometría por defecto y barra $\alpha$ de 0.05 a 0.95 en pasos de 0.15. Registre T30, C50 y D50.

Lo que debe observarse:

- $T_{30}$ decrece monótonamente conforme sube $\alpha$ (consistente con Sabine: $T \approx 0.161\,V/(S\alpha)$).
- $D_{50}$ y $C_{50}$ crecen: menos energía tardía significa mayor proporción de energía útil.
- La voz gana inteligibilidad pero pierde "cuerpo": el compromiso central del diseño de salas polivalentes.

Comparación con Sabine, para la sala por defecto: $V = 4050$ m³, $S = 1800$ m². Con $\alpha = 0.5$, la predicción de Sabine es $T \approx 0.725$ s y la de Eyring $T \approx 0.523$ s. Contrástela con el T30 simulado; discrepancias moderadas son esperables porque Sabine supone campo perfectamente difuso y absorción uniformemente distribuida.

### B. Convergencia con el orden de reflexiones

Fije $\alpha = 0.3$ y varíe `max_order` de 1 a 10, anotando T30, C80 y el tiempo de respuesta de la interfaz.

Lo esperable: los parámetros se estabilizan a partir de orden 4–6, mientras el costo computacional sigue creciendo. Este experimento justifica empíricamente el valor por defecto de 3 y enseña un principio general de simulación numérica: el orden útil es aquel a partir del cual la métrica de interés deja de cambiar significativamente.

### C. Dependencia espectral

Ponga el modo de gráfica en **"Todas las frecuencias"** y observe la superposición de las seis bandas.

Con `pra.Material(alpha)` la absorción de las superficies es idéntica en todas las bandas, así que las diferencias visibles provienen casi exclusivamente de la **absorción del aire**, que crece con la frecuencia y con la humedad relativa. Por eso la banda de 4 kHz decae más rápido que la de 125 Hz.

En una sala real la separación entre bandas es mucho mayor y de signo frecuentemente opuesto en graves (donde las butacas absorben poco y aparecen modos propios). Este contraste es útil precisamente para discutir las limitaciones del modelo.

### D. Distancia crítica

Aumente el largo a 50 m manteniendo $\alpha = 0.2$ y observe $L_p$. Calcule la distancia crítica:

$$r_c = \sqrt{\frac{QR}{16\pi}}, \qquad R = \frac{S\alpha}{1-\alpha}$$

Compruebe que los receptores más lejanos reciben un nivel casi idéntico entre sí: más allá de $r_c$ domina el campo reverberante y alejarse deja de reducir el nivel.

### E. Contraste con mediciones reales

Configure las dimensiones reales del Centro de las Artes y ajuste $\alpha$ hasta que el T30 simulado coincida con el T30 medido en la banda de 1 kHz. Ese $\alpha$ es el **coeficiente de absorción equivalente** de la sala.

Después compare **D50 y C80**: normalmente no coincidirán tan bien, porque el ajuste de $\alpha$ solo calibra la energía total, no su distribución temporal. Es un buen recordatorio de que un modelo calibrado en un parámetro no queda calibrado en todos.

---

## 3.3 Lectura de las gráficas

### Curva EDC

- **Eje vertical:** nivel de presión sonora absoluto en dB, obtenido desplazando la EDC normalizada por $L_p$. Cambiar $L_W$ desplaza la curva completa sin alterar su pendiente.
- **Pendiente:** proporcional al inverso del tiempo de reverberación. Más vertical significa sala más seca.
- **Líneas discontinuas:** umbrales de ajuste de EDT (−10 dB, rojo), T20 (−25 dB, verde) y T30 (−35 dB, naranja) medidos desde $L_p$.
- **Meseta final:** artefacto numérico donde la energía remanente se agota; no es un fenómeno físico.

Señal de alerta: si la curva no cruza la línea naranja, el T30 reportado será `NaN` para ese receptor y el promedio se calculará solo con los restantes.

### Panel de barras

- **Izquierda (tiempos):** EDT, T20 y T30 en segundos. Valores muy dispares entre sí indican decaimiento no exponencial (dos pendientes), típico de espacios acoplados.
- **Centro (claridad):** C50 y C80 en dB, con línea de cero marcada. Positivo significa que domina la energía temprana.
- **Derecha ($L_p$):** nivel promedio entre los cinco receptores. Depende directamente de $L_W$.

---

## 3.4 Resolución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| ⚠️ Error al descargar el audio | Sin red, o URL cambiada | Verifique conexión; ver `assets/README.md` para usar archivos locales |
| Los botones no producen sonido | `sounddevice` sin dispositivo de salida, o ejecución remota | Ejecute localmente; en Linux instale `libportaudio2` |
| La interfaz tarda mucho | `max_order` alto y estímulo largo | Baje el orden a 3–4; recorte el audio |
| T30 aparece como `nan` | El decaimiento no alcanza −35 dB | Baje $\alpha$, suba `max_order` o use un estímulo más largo |
| Error de índice al reducir el largo | Receptores fuera del recinto | Mantenga el largo ≥ 20 m (ver limitación 2 en `05-limitaciones.md`) |
| `ModuleNotFoundError: pyroomacoustics` | Entorno sin activar | Active el venv o use `uv run` |
| Curvas EDC casi superpuestas | Comportamiento esperado con absorción uniforme | Ver experimento C |

---

## 3.5 Uso en clase

**Como demostración (15 min):** ejecutar en modo `marimo run`, hacer el experimento A en vivo y pedir a los estudiantes que predigan la dirección del cambio de cada parámetro antes de mover el control.

**Como práctica de laboratorio (2 h):** asignar los experimentos A, B y C, exigiendo tabla de resultados, contraste con la fórmula de Sabine y discusión de discrepancias.

**Como componente de proyecto:** combinar con el repositorio de mediciones experimentales para un ejercicio de validación de modelo, cuyo entregable sea el $\alpha$ equivalente ajustado y un análisis de en qué parámetros el modelo falla y por qué.
