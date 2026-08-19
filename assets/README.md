# Estímulos anecoicos

La aplicación descarga por defecto dos señales alojadas en GitHub mediante `urllib.request`:

| Estímulo | Uso | Parámetros relevantes |
|---|---|---|
| Voz humana | Evaluar inteligibilidad | D50, C50 |
| Saxofón | Evaluar claridad musical | C80, EDT |

## Requisitos del material

Para que la auralización sea acústicamente válida, los estímulos deben ser **anecoicos**: grabados en cámara sin reflexiones. Si la grabación ya contiene reverberación, la convolución superpone dos salas y los resultados perceptuales dejan de ser interpretables.

Especificaciones recomendadas: WAV PCM, 44.1 o 48 kHz, 16 o 24 bits, mono o estéreo (el cuaderno mezcla a mono), duración de 5 a 15 segundos.

## Usar archivos locales en lugar de las URL

En la celda de selección de sonido, reemplace las URL por rutas locales y sustituya el bloque de descarga:

```python
fs, audio_org = wavfile.read("assets/voz.wav")
```

Los archivos `.wav` dentro de `assets/` están exceptuados del `.gitignore`, de modo que pueden versionarse si su licencia lo permite.

## Fuentes públicas de material anecoico

- Biblioteca anecoica de la Universidad Aalto (Pätynen et al.)
- Odeon anechoic recordings
- OpenAIR Library (York) — principalmente respuestas al impulso, útiles como referencia de contraste
