# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "marimo>=0.23.3",
#     "matplotlib>=3.10.9",
#     "numpy>=2.4.4",
#     "pyroomacoustics>=0.10.1",
#     "scipy>=1.17.1",
#     "sounddevice>=0.5.5",
# ]
# ///

import marimo

__generated_with = "0.23.5"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    import pyroomacoustics as pra
    import sounddevice as sd
    import scipy.io.wavfile as wavfile
    import scipy.signal as signal
    import urllib.request
    import io

    return io, mo, np, plt, pra, sd, signal, urllib, wavfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(f"""
    #Simulación auditiva de los parámetros acústicos de un auditorio

    Esta aplicación permite realizar una simulación tanto visual como auditiva de distintos parámetros para el estudio acústico de un auditorio.

    Los parámetros simulados incluyen:

    - EDT (Early Decay Time)
    - Curva de decaimiento
    - T20 (Tiempo de reverberación a 20 dB)
    - T30 (Tiempo de reverberación a 30 dB)
    - D50 (Dependencia de la distancia)
    - C50 (Coherencia de la señal)
    - C80 (Coherencia de la señal)
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Índice de Contenidos

    * [Fundamentos Teóricos y Matemáticos de la Simulación](#fundamentos-teóricos-y-matemáticos-de-la-simulación-acústica)
    * [1. Respuesta al Impulso de la Habitación (RIR)]()
        * [1.1. Filtrado en Bandas de Octava]()
    * [2. Integración de Schroeder]()
        * [2.1. Curva de Decaimiento de Energía (EDC)]()
    * [3. Tiempos de Reverberación]()
        * [3.1. EDT (Early Decay Time)]()
        * [3.2. T20 y T30]()
    * [4. Parámetros de Claridad e Inteligibilidad]()
    * [5. Nivel de Presión Sonora Absoluto]()
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Fundamentos Teóricos y Matemáticos de la Simulación Acústica

    Para tener un mejor entendimiento de lo que ocurre detras de la simulación, a continuación se cuenta con la explicación de las bases fundamentales para comprender los parámetros acústicos calculados en la simulación.

    ## 1. Respuesta al Impulso de la Habitación (RIR)

    El análisis acústico del recinto se modela asumiendo el auditorio como un sistema lineal e invariante en el tiempo (LTI). Tomando esto en cuenta, el comportamiento acústico entre una fuente y un receptor queda completamente caracterizado por la Respuesta al Impulso de la Habitación (RIR). Como referencia se utiliza la norma ISO 3382-1, en esta misma mas bien el comportamiento acústico queda completamente caracterizado por la presión sonora instantánea de la respuesta al impulso, denotada por la norma ISO como $p(t)$.

    ### 1.1. Filtrado en Bandas de Octava

    En la simulación se tiene que la "Respuesta al Impulso", denotada como $h(t)$, es la señal que captura el micrófono cuando la fuente emite un impulso ideal de Dirac $\delta(t)$. Esta señal contiene el sonido directo, las reflexiones tempranas y la cola reverberante estocástica.

    Para cumplir con la normativa ISO 3382, la RIR no se analiza en todo el espectro simultáneamente, sino que se filtra en bandas de octava. El código utiliza un **Filtro Butterworth de paso banda** de orden 4. Las frecuencias de corte inferior ($f_l$) y superior ($f_u$) para una frecuencia central ($f_c$) están dadas por:

    $$f_{l}=\frac{f_{c}}{\sqrt{2}}$$

    $$f_{u}=f_{c}\sqrt{2}$$

    ### 1.2 Integración de Schroeder y Curva de Decaimiento de Energía (EDC)

    Para obtener decaimientos suaves y evaluar los tiempos de reverberación con precisión analítica, se descarta la evaluación directa de la RIR y se emplea la integral de Schroeder. Esta curva representa la energía remanente en la sala en un instante $t$:

    $$EDC(t)=\int_{t}^{\infty}h^{2}(\tau)d\tau$$

    En el código, para su análisis y graficación, esta curva se normaliza respecto a la energía total inicial y se transforma a una escala logarítmica de decibelios:

    $$EDC_{dB}(t)=10\log_{10}\left(\frac{EDC(t)}{EDC(0)}\right)$$

    ## 1.3 Tiempos de Reverberación (EDT, T20, T30)

    El tiempo de reverberación estandarizado ($RT_{60}$) es el tiempo que tarda la energía acústica en decaer 60 dB tras apagarse la fuente. Como en las mediciones reales (o simulaciones con ruido de fondo) es difícil alcanzar una caída limpia de 60 dB, se extrapola mediante regresión lineal sobre la curva $EDC_{dB}(t)$ en distintos intervalos:

    ### 3.1. EDT (Early Decay Time)


    ### 3.2. T20 y T30

    * **EDT (Early Decay Time):** Se extrapola midiendo la pendiente entre $0\text{ dB}$ y $-10\text{ dB}$. Se relaciona fuertemente con la percepción subjetiva de la reverberación.
    * **T20:** Se extrapola midiendo la pendiente entre $-5\text{ dB}$ y $-25\text{ dB}$.
    * **T30:** Se extrapola midiendo la pendiente entre $-5\text{ dB}$ y $-35\text{ dB}$. Es el estimador más robusto del $RT_{60}$ clásico.

    ### 1.4 Parámetros de Energía Temprana y Tardía

    La inteligibilidad y claridad del sonido dependen del balance de energía que llega en los primeros milisegundos (sonido útil) frente a la energía tardía (enmascaramiento).

    **Definición (D50):**
    Mide el porcentaje de energía que llega en los primeros 50 ms. Es un indicador directo de la inteligibilidad de la palabra hablada.


    $$D_{50}=\left(\frac{\int_{0}^{0.05}h^{2}(t)dt}{\int_{0}^{\infty}h^{2}(t)dt}\right)\times100\%$$

    **Claridad de la Voz (C50) y Claridad Musical (C80):**
    Relación logarítmica entre la energía temprana y la energía tardía. El límite de tiempo se establece en 50 ms para la voz y 80 ms para la música, dado que las notas musicales se benefician de reflexiones ligeramente más tardías.


    $$C_{50}=10\log_{10}\left(\frac{\int_{0}^{0.05}h^{2}(t)dt}{\int_{0.05}^{\infty}h^{2}(t)dt}\right)\text{ dB}$$

    $$C_{80}=10\log_{10}\left(\frac{\int_{0}^{0.08}h^{2}(t)dt}{\int_{0.08}^{\infty}h^{2}(t)dt}\right)\text{ dB}$$

    ### 1.5 Campo Sonoro Absoluto: Nivel de Presión Sonora ($L_p$)

    Mientras que los parámetros anteriores son relativos a la propia RIR, para determinar el volumen real en un asiento se utiliza la dispersión de la energía en espacios cerrados (Campo directo + Campo reverberante).

    Primero, se define la **Constante de la Sala ($R$)**, que cuantifica la capacidad de absorción total del recinto en función de su superficie total ($S$) y su coeficiente de absorción promedio ($\alpha$):


    $$R=\frac{S\alpha}{1-\alpha}$$

    Con esto, aplicamos la **Ley del Cuadrado Inverso modificada para recintos cerrados**, la cual relaciona el Nivel de Potencia de la fuente ($L_W$), el factor de directividad ($Q$, donde $Q=1$ para fuente omnidireccional), y la distancia fuente-receptor ($r$):


    $$L_{p}=L_{W}+10\log_{10}\left(\frac{Q}{4\pi r^{2}}+\frac{4}{R}\right)$$

    Esta ecuación dicta el nivel base al cual se ajusta (desplaza) la gráfica logarítmica de la EDC en la interfaz, representando fielmente la presión sonora absoluta que golpea al oyente.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Sustituye estas URLs por los enlaces "Raw" de tus audios en GitHub
    url_voz = "https://github.com/LuAViVA/Proyecto-Acustica/raw/97c3b02797b7fbf216960295b8ea2b6303fdc51e/voz.wav"
    url_saxo = "https://github.com/LuAViVA/Proyecto-Acustica/raw/97c3b02797b7fbf216960295b8ea2b6303fdc51e/saxof%C3%B3n.wav"

    sonido_widget = mo.ui.dropdown(
        options={"Voz Humana": url_voz, "Saxofón": url_saxo},
        value="Voz Humana",
        label="Selecciona el sonido a evaluar:"
    )

    mo.md(
        f"""
        ## Selección de Sonido

        Selecciona el sonido que deseas evaluar en la simulación acústica del auditorio:

        {sonido_widget}
        """
    )
    return (sonido_widget,)


@app.cell
def _(mo):
    mo.md(r"""
    Para escuchar el sonido sin pasar por la simulación del auditorio presione el siguiente botón.
    """)
    return


@app.cell
def _(io, mo, np, sd, sonido_widget, urllib, wavfile):
    url_archivo = sonido_widget.value

    try:
        # Se descarga el archivo directamente a la memoria RAM
        respuesta = urllib.request.urlopen(url_archivo)
        audio_bytes = respuesta.read()

        # Se lee como si fuera un archivo físico
        fs, audio_org = wavfile.read(io.BytesIO(audio_bytes))

        # Procesamiento básico del audio
        audio_org = audio_org.astype(np.float32)
        if audio_org.ndim > 1:
            audio_org = audio_org.mean(axis=1) # Convertir estéreo a mono
        audio_org = audio_org / np.max(np.abs(audio_org))

        estado = mo.md("✅ *Audio cargado desde la nube exitosamente.*")

    except Exception as e:
        estado = mo.md(f"⚠️ **Error al descargar el audio**")
        fs = 44100
        audio_org = np.zeros(fs)

    def reproducir_audio_seco(val):
        sd.play(audio_org, fs)

    btn_seco = mo.ui.button(
        label = f"🎵 1. Audio original", 
        on_click = reproducir_audio_seco
    )

    btn_seco
    return audio_org, estado, fs


@app.cell
def _(estado):
    estado
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Simulación

    A continuación se presentan los parámetros que se pueden editar para ver cómo cambia el audio en la simulación. Entre los parámetros que se pueden editar tenemos:

    ## Rango auditovo normal:

    | Decibelios (dB) | Comparación de sonidos                                   |
    |-----------------|----------------------------------------------------------|
    | 10 dB           | Alguien respirando                                       |
    | 30 dB           | Habla susurrando                                         |
    | 60 dB           | Conversaciones típicas                                   |
    | 80 dB           | Herramientas eléctricas, pasando motos                   |
    | 100 dB          | Concierto de música en directo, motosierra               |
    | 120+ dB         | Martillo neumático, fuegos artificiales, motor a reacción|
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    # Parámetros Editables de la Simulación Acústica

    La herramienta de simulación cuenta con un panel de control interactivo que permite al usuario modificar en tiempo real las propiedades geométricas, físicas y algorítmicas del auditorio. A continuación, se detallan los parámetros disponibles, sus límites de operación y el incremento de ajuste (paso).

    ### Resumen de Parámetros

    | Categoría     | Parámetro                        | Rango Operativo             | Paso (*Step*) | Valor por Defecto |
    | :---          | :---:                            | :---:                       | :---:         | :---:             |
    | **Dimensiones** | Ancho de la sala                 | 5.0 m – 30.0 m              | 1.0 m         | 18.0 m            |
    | **Dimensiones** | Largo de la sala                 | 10.0 m – 50.0 m             | 1.0 m         | 30.0 m            |
    | **Dimensiones** | Alto de la sala                  | 3.0 m – 15.0 m              | 0.5 m         | 7.5 m             |
    | **Física**      | Potencia de Fuente ($L_W$)       | 60 dB – 140 dB              | 1 dB          | 100 dB            |
    | **Física**      | Coeficiente de Absorción ($\alpha$) | 0.05 – 0.95                 | 0.05          | 0.50              |
    | **Motor**       | Orden de Reflexiones (ISM)       | 1 – 10                      | 1             | 3                 |
    | **Análisis**    | Frecuencia ISO                   | 125, 250, 500, 1000, 2000, 4000 Hz | N/A          | 1000 Hz           |
    | **Análisis**    | Modo de Gráfica EDC              | Única / Todas las bandas    | N/A           | Solo la seleccionada |


    ---

    ### Descripción Funcional de las Variables

    #### 1. Dimensiones Físicas del Recinto
    Define el volumen total del auditorio ($V = Ancho \times Largo \times Alto$). De acuerdo con la ecuación de Sabine y la teoría de campos difusos, alterar este volumen tiene un impacto directo sobre los tiempos de reverberación (EDT, T20, T30) y determina la distancia crítica a la que el campo directo se iguala con el campo reverberante. Por defecto, la simulación cuenta con las dimensiones del auditorio "Centro de las artes" del Instituto Tecnológico de Costa Rica.

    #### 2. Propiedades Físicas y Acústicas
    * **Nivel de Potencia Sonora ($L_W$):** Representa la energía acústica total emitida por la fuente (ej. un orador humano $\approx 60-70\text{ dB}$, un arreglo de altavoces $\approx 110-130\text{ dB}$). Modifica el Nivel de Presión Sonora ($L_p$) absoluto en la sala, pero no altera los tiempos de decaimiento relativo.
    * **Coeficiente de Absorción ($\alpha$):** Promedio de absorción de los materiales de los límites de la sala. Un valor cercano a $0.05$ representa superficies altamente reflectantes (ej. concreto o vidrio), mientras que valores cercanos a $0.95$ simulan superficies de alta absorción (ej. paneles acústicos porosos o público densamente sentado).

    #### 3. Configuración del Motor y Análisis
    * **Orden Máximo de Reflexiones:** Parámetro fundamental del Método de Fuentes Imagen (Image Source Method). Define la cantidad máxima de rebotes que el algoritmo trazará para cada rayo de sonido. Un orden mayor aumenta exponencialmente la precisión de la cola reverberante tardía y los parámetros de claridad ($C_{50}$, $C_{80}$), a costa de un mayor tiempo computacional.
    * **Frecuencia ISO (Hz):** Aplica un filtro pasabanda de Butterworth a la Respuesta al Impulso antes del procesamiento energético. Permite evaluar el comportamiento de la sala desde los graves profundos ($125\text{ Hz}$) hasta los agudos ($4000\text{ Hz}$), cumpliendo con la normativa ISO 3382-1.
    * **Modo de Gráfica:** Permite alternar entre el estudio detallado de una única banda de frecuencia (con sus respectivos umbrales normativos) o una superposición global para identificar coloraciones acústicas indeseadas en el espectro completo.

    ***
    """)
    return


@app.cell
def _(get_reset, mo):
    _ = get_reset()

    # Variables
    ui_ancho = mo.ui.number(start=5.0, stop=30.0, step=1.0, value=18.0, label="Ancho (m)")
    ui_largo = mo.ui.number(start=10.0, stop=50.0, step=1.0, value=30.0, label="Largo (m)")
    ui_alto = mo.ui.number(start=3.0, stop=15.0, step=0.5, value=7.5, label="Alto (m)")

    ui_lw = mo.ui.number(start=10.0, stop=130.0, step=1.0, value=100.0, label="Potencia de Fuente (Lw) [dB]")
    ui_abs = mo.ui.number(start=0.05, stop=0.95, step=0.05, value=0.5, label="Coef. Absorción")
    ui_orden = mo.ui.number(start=1, stop=10, step=1, value=3, label="Orden reflexiones (ISM)")

    ui_freq = mo.ui.dropdown(options=[125, 250, 500, 1000, 2000, 4000], value=1000, label="Frecuencia ISO (Hz)")

    ui_modo_grafica = mo.ui.radio(
        options=["Solo la seleccionada", "Todas las frecuencias"], 
        value="Solo la seleccionada", 
        label="Modo de gráfica EDC"
    )

    ui_reset = mo.ui.button(label="🔄 Reiniciar Simulación", on_click=lambda: None)  # Aquí puedes agregar la lógica de reinicio si es necesario



    panel_controles = mo.md(
        f"""
        ### 🎛️ Panel de Control Acústico

        **1. Dimensiones de la Sala:** {ui_ancho} | {ui_largo} | {ui_alto}

        **2. Propiedades Físicas:** {ui_lw} | {ui_abs} 

        **3. Motor de Simulación:** {ui_orden} | {ui_freq}

        **4. Visualización:** {ui_modo_grafica}
        """
    )

    panel_controles
    return (
        ui_abs,
        ui_alto,
        ui_ancho,
        ui_freq,
        ui_largo,
        ui_lw,
        ui_modo_grafica,
        ui_orden,
    )


@app.cell
def _(mo):
    # Creamos un estado que actuará como gatillo (inicia en 0)
    get_reset, set_reset = mo.state(0)

    # El botón simplemente suma 1 al estado cada vez que se hace clic
    btn_reiniciar = mo.ui.button(
        label="🔄 Reiniciar Parámetros", 
        on_click=lambda _: set_reset(get_reset() + 1)
    )

    btn_reiniciar
    return (get_reset,)


@app.cell
def _(btn_reproducir_simulacion, mo):
    btn_sim = mo.ui.button(
            label="🔊 2. Escuchar con acústica del auditorio", 
            on_click=btn_reproducir_simulacion
        )

    btn_sim
    return


@app.cell
def _():
    return


@app.cell
def _(
    audio_org,
    fs,
    np,
    pra,
    sd,
    ui_abs,
    ui_alto,
    ui_ancho,
    ui_largo,
    ui_orden,
):
    # Creación de la sala y simulación acústica
    _mat = pra.Material(ui_abs.value)
    _room_dim = [ui_ancho.value, ui_largo.value, ui_alto.value]

    room_sim = pra.ShoeBox(
        _room_dim, fs=fs, materials=_mat, max_order=ui_orden.value,
        air_absorption=True, ray_tracing=True, temperature=20, humidity=50             
    )

    _source_loc = [ui_ancho.value / 2, 4.0, 1.5]
    _asientos = [
        [4.0, 10.0, 1.2], [ui_ancho.value - 4.0, 12.0, 1.2], 
        [ui_ancho.value / 2, 18.0, 1.2], # Asiento central
        [5.0, ui_largo.value - 5.0, 1.2], [ui_ancho.value - 5.0, ui_largo.value - 4.0, 1.2]  
    ]

    room_sim.add_source(_source_loc, signal=audio_org)
    room_sim.add_microphone_array(pra.MicrophoneArray(np.array(_asientos).T, fs))
    room_sim.simulate()

    senal_out = room_sim.mic_array.signals[2]
    if np.max(np.abs(senal_out)) > 0:
        senal_out = senal_out / np.max(np.abs(senal_out))

    def btn_reproducir_simulacion(val):
        sd.play(senal_out, fs)

    return btn_reproducir_simulacion, room_sim


@app.cell
def _():
    return


@app.cell
def _(
    fs,
    np,
    room_sim,
    signal,
    ui_abs,
    ui_alto,
    ui_ancho,
    ui_freq,
    ui_largo,
    ui_lw,
):
    def _filtro_octava(data, fc):
        _fl, _fu = fc / np.sqrt(2), fc * np.sqrt(2)
        _b, _a = signal.butter(4, [_fl/(fs/2), min(_fu/(fs/2), 0.99)], btype='bandpass')
        return signal.filtfilt(_b, _a, data)

    def _calc_tiempo(curva, u_in, u_fin):
        try:
            _i_in, _i_fin = np.where(curva <= u_in)[0][0], np.where(curva <= u_fin)[0][0]
            _m, _ = np.polyfit(np.arange(_i_in, _i_fin)/fs, curva[_i_in:_i_fin], 1)
            return -60.0 / _m
        except IndexError:
            return np.nan 

    room_sim.compute_rir()

    _S = 2 * (ui_ancho.value * ui_largo.value + ui_ancho.value * ui_alto.value + ui_largo.value * ui_alto.value)
    _alpha = ui_abs.value
    _R_sala = (_S * _alpha) / (1 - _alpha) if _alpha < 0.99 else float('inf')
    _src_loc = np.array([ui_ancho.value / 2, 4.0, 1.5]) 

    _temp_res = {'edt':[], 't20':[], 't30':[], 'c50':[], 'c80':[], 'd50':[], 'Lp':[]}

    # Calculo EDC para todas las frecuencias en el asiento central
    _frecuencias_iso = [125, 250, 500, 1000, 2000, 4000]
    curvas_edc_todas = {}
    _rir_central = room_sim.rir[2][0]

    for _f in _frecuencias_iso:
        _rir_filt = _filtro_octava(_rir_central, _f)
        _sq = _rir_filt ** 2
        _edc = np.cumsum(_sq[::-1])[::-1]
        curvas_edc_todas[_f] = 10 * np.log10((_edc / _edc[0]) + 1e-10)

    curva_edc_central = curvas_edc_todas[ui_freq.value]

    # Cálculo de parámetros promedio para todos los micrófonos
    for _i in range(len(room_sim.mic_array.R.T)):
        _rir_filt = _filtro_octava(room_sim.rir[_i][0], ui_freq.value)
        _sq = _rir_filt ** 2
        _edc = np.cumsum(_sq[::-1])[::-1]
        _edc_db = 10 * np.log10((_edc / _edc[0]) + 1e-10)

        _temp_res['edt'].append(_calc_tiempo(_edc_db, 0, -10))
        _temp_res['t20'].append(_calc_tiempo(_edc_db, -5, -25))
        _temp_res['t30'].append(_calc_tiempo(_edc_db, -5, -35))

        _e50_t, _e50_l = np.sum(_sq[:int(0.05*fs)]), np.sum(_sq[int(0.05*fs):])
        _e80_t, _e80_l = np.sum(_sq[:int(0.08*fs)]), np.sum(_sq[int(0.08*fs):])

        _temp_res['c50'].append(10 * np.log10(_e50_t / (_e50_l + 1e-10)))
        _temp_res['d50'].append((_e50_t / (_e50_t + _e50_l)) * 100)
        _temp_res['c80'].append(10 * np.log10(_e80_t / (_e80_l + 1e-10)))

        _r = np.linalg.norm(_src_loc - room_sim.mic_array.R[:, _i])
        _Lp = ui_lw.value + 10 * np.log10((1 / (4 * np.pi * _r**2)) + (4 / _R_sala if _R_sala != float('inf') else 0))
        _temp_res['Lp'].append(_Lp)

    res_acusticos = {k: np.nanmean(v) for k, v in _temp_res.items()}
    return curva_edc_central, curvas_edc_todas, res_acusticos


@app.cell
def _(
    curva_edc_central,
    curvas_edc_todas,
    fs,
    np,
    plt,
    res_acusticos,
    ui_freq,
    ui_modo_grafica,
):
    fig_edc_plot, ax_edc_plot = plt.subplots(figsize=(10, 6))

    if curva_edc_central is not None:
        lp_inicial = res_acusticos['Lp']
        tiempo_edc = np.arange(len(curva_edc_central)) / fs

        if ui_modo_grafica.value == "Todas las frecuencias":
            # Colores estándar de Matplotlib para distinguir bien las bandas
            colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

            for idx, (f_iso, curva) in enumerate(curvas_edc_todas.items()):
                ax_edc_plot.plot(tiempo_edc, curva + lp_inicial, color=colores[idx], linewidth=1.5, alpha=0.8, label=f'{f_iso} Hz')

            titulo = 'Curvas de Decaimiento de Energía (Todas las bandas de octava)'
        else:
            ax_edc_plot.plot(tiempo_edc, curva_edc_central + lp_inicial, color='#1f77b4', linewidth=2, label=f'EDC ({ui_freq.value} Hz)')
            titulo = f'Curva de Decaimiento de Energía (Banda: {ui_freq.value} Hz)'

        # Líneas de umbral normativo
        ax_edc_plot.axhline(y=lp_inicial - 10, color='red', linestyle='--', alpha=0.7, label='Límite EDT (-10 dB)')
        ax_edc_plot.axhline(y=lp_inicial - 25, color='green', linestyle='--', alpha=0.7, label='Límite T20 (-25 dB)')
        ax_edc_plot.axhline(y=lp_inicial - 35, color='orange', linestyle='--', alpha=0.7, label='Límite T30 (-35 dB)')

        ax_edc_plot.set_title(titulo, fontsize=14, fontweight='bold')
        ax_edc_plot.set_xlabel('Tiempo (segundos)', fontsize=12)
        ax_edc_plot.set_ylabel('Nivel de Presión Sonora Absoluto (dB)', fontsize=12)

        ax_edc_plot.set_ylim([lp_inicial - 60, lp_inicial + 5])
        ax_edc_plot.set_xlim([0, tiempo_edc[-1]])

        ax_edc_plot.grid(True, which='both', linestyle=':', linewidth=0.8)

        # Ajustar leyenda si son muchas frecuencias
        if ui_modo_grafica.value == "Todas las frecuencias":
            ax_edc_plot.legend(loc='upper right', fontsize=9, ncol=2)
        else:
            ax_edc_plot.legend(loc='upper right')
    else:
        ax_edc_plot.text(0.5, 0.5, "No hay datos de curva disponibles", ha='center')

    fig_edc_plot
    return


@app.cell
def _(plt, res_acusticos):
    fig_barras_plot, (ax_t, ax_c, ax_lp) = plt.subplots(1, 3, figsize=(15, 5), gridspec_kw={'width_ratios': [3, 2, 1.5]})

    # Tiempos de Reverberación
    nombres_t = ['EDT', 'T20', 'T30']
    vals_t = [res_acusticos['edt'], res_acusticos['t20'], res_acusticos['t30']]
    barras_t = ax_t.bar(nombres_t, vals_t, color=['#1f77b4', '#ff7f0e', '#2ca02c'], alpha=0.85)

    ax_t.set_title('Tiempos de Reverberación', fontsize=13)
    ax_t.set_ylabel('Segundos (s)', fontsize=11)
    ax_t.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in barras_t:
        yval = bar.get_height()
        ax_t.text(bar.get_x() + bar.get_width()/2, yval + 0.05, f'{yval:.2f} s', ha='center', va='bottom', fontweight='bold')

    # Parámetros de Claridad
    nombres_c = ['C50 (Voz)', 'C80 (Música)']
    vals_c = [res_acusticos['c50'], res_acusticos['c80']]
    barras_c = ax_c.bar(nombres_c, vals_c, color=['#9467bd', '#8c564b'], alpha=0.85)

    ax_c.set_title('Índices de Claridad', fontsize=13)
    ax_c.set_ylabel('Decibelios (dB)', fontsize=11)
    ax_c.axhline(0, color='black', linewidth=1) 
    ax_c.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in barras_c:
        yval = bar.get_height()
        offset = 0.5 if yval >= 0 else -1.5
        ax_c.text(bar.get_x() + bar.get_width()/2, yval + offset, f'{yval:.2f} dB', ha='center', va='bottom', fontweight='bold')

    # Nivel de Presión Sonora Absoluto (Lp)
    barra_lp = ax_lp.bar(['Lp Promedio'], [res_acusticos['Lp']], color=['#d62728'], alpha=0.85, width=0.4)

    ax_lp.set_title('Nivel de Presión Sonora', fontsize=13)
    ax_lp.set_ylabel('Decibelios (dB)', fontsize=11)
    ax_lp.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in barra_lp:
        yval = bar.get_height()
        ax_lp.text(bar.get_x() + bar.get_width()/2, yval + 1.0, f'{yval:.1f} dB', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()

    fig_barras_plot
    return


if __name__ == "__main__":
    app.run()
