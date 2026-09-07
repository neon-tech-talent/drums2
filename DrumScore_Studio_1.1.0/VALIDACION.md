# Validación de la entrega 1.1.0

Fecha: 7 de septiembre de 2026.

Entorno de ejecución de las pruebas: Linux, Python 3.12.13, Pillow 12.3.0, NumPy 2.3.5, SciPy 1.17.0 y Node.js 24.19.0. Motor de notación y síntesis: el alphaTab 1.8.4 del ZIP original.

## Resultados

| Área | Resultado comprobado |
| --- | --- |
| Servidor y recursos locales | HTML, JavaScript, fuentes y SoundFont responden correctamente. |
| Guardado | Crear, actualizar sin duplicar, detener y reiniciar servidor, recuperar el título, los ajustes y la cuadrícula corregida. |
| Imagen de rock | 2 compases y 25 golpes; se compararon posiciones e instrumentos esperados. |
| Imagen de fill | 2 compases y 20 golpes; caja, tom alto, tom medio y tom base correctos, sin golpes adicionales en el fill. |
| Página con dos sistemas | 4 compases y 45 golpes, también con rotación de −5° y +5°. |
| Imágenes no válidas | Una imagen blanca y datos no gráficos son rechazados. Un compás vacío conserva sus silencios. |
| Cuadrícula MusicXML | Duración correcta en 4/4, 3/4, 6/8, 9/8 y 12/8 con distintas subdivisiones; notas simultáneas y tresillos. |
| Importación | Los nueve ejemplos digitales cargan con el motor real. Las cuadrículas generadas en Python son importadas por alphaTab y producen los MIDI esperados. |
| Sonidos | En el ejemplo rock, los primeros golpes simultáneos generan MIDI 36 y 42. La señal sintetizada tiene muestras finitas, amplitud mayor que cero y sin saturación en el tramo medido. |
| WAV al tempo original | Dos compases a 120 BPM: 4,0011 s. |
| WAV a mitad de tempo | El mismo tramo a 60 BPM: 8,0007 s. |
| WAV al doble de tempo | El mismo tramo a 240 BPM: 2,0013 s. |
| WAV de un bucle avanzado | Un compás seleccionado desde el tercer compás: 2,0013 s. |
| Mezcla | Volumen maestro en cero genera silencio; incluir metrónomo cambia la señal. |
| Formato de audio | Cabecera RIFF/WAV, PCM estéreo, 44.100 Hz y 16 bits; conversión y límites de muestras correctos. |
| Controles con DOM simulado | Bucle A-B, desactivación, navegación, límites de tempo, Espacio para transporte, conservación de tempo al cambiar de pista y visualización de la pista seleccionada. |
| Archivos | Los módulos JavaScript y Python pasan la validación de sintaxis. Los controles hacen referencia a elementos presentes en el HTML y no quedan recursos externos de interfaz. |

Las pequeñas diferencias de duración corresponden a los bloques de 64 muestras del sintetizador.

## Lo que estas pruebas no certifican

No son una prueba visual de extremo a extremo en un navegador. No se verificó físicamente Windows, la salida de los parlantes, las políticas de audio del navegador, ni partituras reales arbitrarias. Tampoco se midió una tasa general de precisión del OMR. Los resultados de imagen anteriores corresponden a ejemplos sintéticos con notas conocidas.

## Comprobación en Windows

1. Iniciar con `iniciar_sistema.bat` y reproducir un ritmo de ejemplo. Confirmar bombo, caja y charles y su seguimiento visual.
2. Cambiar el tempo durante la reproducción, pausar y reanudar.
3. Marcar A y B en compases diferentes y escuchar dos vueltas del bucle.
4. Escanear una imagen propia, corregir una nota, cargarla, guardar y reiniciar para recuperarla.
5. Exportar un tramo WAV, escuchar la vista previa y descargarlo.

Si aparece un problema, conservar el mensaje visible y el de la consola junto con el archivo musical o imagen que lo provoca.
