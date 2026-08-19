# Guía de contribución

## Antes de empezar

Este cuaderno es un archivo `.py` de marimo, no un `.ipynb`. **Edítelo siempre con `marimo edit`**, nunca a mano en un editor de texto: marimo mantiene el orden topológico de las celdas y la consistencia del grafo de dependencias.

```bash
uv run marimo edit app/simulacion_acustica.py
```

## Convenciones

- **Variables locales con prefijo `_`.** En marimo esto las excluye del grafo global y evita colisiones entre celdas. Toda variable auxiliar debe llevarlo.
- **Nombres en español** para variables de dominio (`curva_edc_central`, `res_acusticos`), coherente con la documentación.
- **Una responsabilidad por celda.** Si una celda hace simulación y graficación a la vez, divídala.
- **Documentar las suposiciones físicas** en Markdown dentro del propio cuaderno, no solo en `docs/`.

## Checklist antes de un pull request

1. El cuaderno abre sin errores con los valores por defecto.
2. `python -m py_compile app/simulacion_acustica.py` pasa.
3. Se probó al menos un caso extremo de cada control modificado (mínimo y máximo).
4. Si se cambió el rango de un widget, se actualizó `docs/04-parametros.md` y la tabla del README.
5. Si se añadió una suposición física, se documentó en `docs/05-limitaciones.md`.

## Áreas donde las contribuciones son especialmente bienvenidas

- Materiales con absorción dependiente de la frecuencia.
- Posiciones de butacas parametrizadas por fracción del largo (ver limitación 5.2).
- Exportación de resultados a CSV y de la RIR a WAV.
- Reemplazo de `sounddevice` por `mo.audio()` para permitir despliegue web.
- Validación contra mediciones reales adicionales.
