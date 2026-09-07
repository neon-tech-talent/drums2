# Cambios y traspaso · DrumScore Studio 1.1.0

## Correcciones confirmadas en el proyecto recibido

- **Instrumentos desplazados:** los ejemplos y los generadores usaban números General MIDI de base 0 directamente dentro de `midi-unpitched`, que exige base 1. Se corrigieron los nueve MusicXML y los generadores. Ahora un charles cerrado produce MIDI 42, la caja 38 y el bombo 36. Los archivos externos importados se respetan: no se les aplica otra conversión arbitraria.
- **Versión real:** el archivo incluido es alphaTab **1.8.4 (build 34)**, aunque el informe anterior decía 1.3.0. Se conserva el binario existente.
- **WAV:** la exportación anterior pasaba una URL en `soundFonts` donde se esperan bytes y no aplicaba la velocidad seleccionada. El nuevo módulo genera MIDI con el motor incluido, ajusta los eventos de tempo y usa AlphaSynth con salida offline. Mantiene los cambios de tempo y las repeticiones del archivo. Codifica PCM por bloques, permite cancelar y muestra la duración real.
- **Bucle:** se activa `isLooping`, además de establecer `playbackRange`. Se limpian las marcas al cargar otra partitura. La navegación usa las ocurrencias de reproducción generadas por alphaTab y contempla repeticiones.
- **Duración:** se dejó de interpretar ticks MIDI como milisegundos. Se integra el mapa de tempo y luego se usa la posición informada por el reproductor.
- **Visualización:** se utilizan eventos MIDI NoteOn reales de la pista de percusión seleccionada. Se eliminó el uso de `PercussionArticulation.getArticulation`, que no existe en el binario recibido.
- **Teclado:** Espacio queda para reproducir/pausar; B para el bombo. Se ignoran atajos en campos de entrada y modales. Se agregaron respuesta táctil, foco de teclado y control de volumen para los pads.
- **Carga y errores:** validación de archivos antes de sustituir la sesión, control de respuestas tardías, recuperación ante errores de carga y controles dependientes de la preparación del reproductor.

## Funciones completadas

- Biblioteca local persistente: `GET/POST /api/scores`, `GET /api/scores/{id}`, escrituras atómicas y conservación de identificadores al actualizar.
- Escaneos guardados con matriz editable y configuración. Los digitales se guardan como bytes codificados en base64.
- Compilación centralizada de cuadrículas en `score_grid.py`, con validación de compás, subdivisión, notas simultáneas y numeración MIDI.
- Subdivisiones de corcheas, semicorcheas, fusas y tresillos uniformes compatibles; selector de tempo, título y compás.
- Editor por compás con once instrumentos y copia del compás anterior.
- Detección óptica de varios pentagramas, corrección de inclinación, eliminación de líneas/plicas y clasificación por posición. Los dos ejemplos sintéticos se actualizaron para que su posición visual de caja y toms coincida con los instrumentos y el MusicXML.
- Resultados ópticos revisables: se rechazan imágenes sin pentagrama o notas distinguibles; se señalan compases ambiguos; no se inventa un BPM ni se repite automáticamente un compás vacío.
- Servidor concurrente que sirve desde la carpeta del proyecto, inicia desde cualquier ubicación y sigue limitado a la máquina local. Valida solicitudes y tamaños, y no publica la carpeta de partituras como directorio estático.
- Recursos de interfaz locales, sin las solicitudes anteriores a Google Fonts.
- Scripts de preparación y arranque de Windows, requisitos y documentación actualizados.

## Estructura adicional

- `js/offlineAudio.js`: generación MIDI, síntesis offline y codificación PCM.
- `score_grid.py`: modelo validado de cuadrícula y generación de MusicXML.
- `data/scores/`: se crea durante el uso para conservar las partituras. No se incluyen datos personales en esta entrega.
- `tests/test_audio.mjs`, `tests/test_controls.mjs`: pruebas de motor y controles.
- `test_system.py`: pruebas funcionales de servidor, almacenamiento y reconocimiento.

## Límites y siguiente validación

Se probaron los motores y los flujos de datos en Linux con Python 3.12 y Node.js 24. La lógica de interfaz tiene pruebas con un DOM simulado. **No se ejecutó una sesión visual en navegador ni el arranque en Windows**. El paso siguiente es abrir el ZIP en Windows y verificar reproducción, seguimiento visual, carga de archivos propios y audio del navegador.

El OMR geométrico sigue siendo asistido; no equivale a una transcripción óptica universal. No incluye OCR de texto ni interpretación completa de compases cambiantes, polirritmias, ligaduras o manuscritos desde imágenes. Estos casos requieren revisión manual o una fuente MusicXML/Guitar Pro. La muestra real Lovesong mencionada en el informe no se recibió en el ZIP; no se pudo reproducir esa afirmación de exactitud.

No se creó un repositorio remoto, no se desplegó el proyecto y no se modificó una instalación de Antigravity. Para continuar, abrir esta carpeta en Antigravity y conservar el contenido de `data/scores/`.

## Referencias técnicas

- [W3C: numeración de midi-unpitched](https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/midi-unpitched/)
- [alphaTab: opciones de exportación y bytes del SoundFont](https://docs.alphatab.net/docs/reference/types/synth/audioexportoptions)
- [alphaTab: eventos MIDI de reproducción](https://docs.alphatab.net/docs/reference/api/midieventsplayed)

El código se contrastó con las clases públicas del archivo alphaTab incluido en este proyecto, conservando su versión y recursos.
