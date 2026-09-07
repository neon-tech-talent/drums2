# DrumScore Studio · 1.1.0

Aplicación local para leer partituras de batería, escucharlas, practicar por compases y exportar audio WAV. Conserva el diseño y los recursos del proyecto original.

## Abrir en Windows

1. Extraé todo el ZIP en una carpeta. No abras la aplicación desde dentro del archivo comprimido.
2. Necesitás Python 3.10 o superior. Si ya usabas la versión anterior, probablemente ya esté instalado.
3. La primera vez, ejecutá **instalar_dependencias.bat**. Instala Pillow, NumPy y SciPy para el lector de imágenes y necesita internet. Si ya tenés estas dependencias, podés omitir este paso.
4. Ejecutá **iniciar_sistema.bat**. Se abrirá el navegador en `http://localhost:8585`, o en otro puerto disponible si ese está ocupado.
5. Dejá abierta la consola mientras usás la aplicación. Cerrala o presioná Ctrl+C para detenerla.

Para abrir desde una terminal: `python server.py`. Para elegir un puerto: `python server.py --port 8888`. Para iniciar sin abrir el navegador: `python server.py --no-browser`.

No requiere una cuenta ni Antigravity para funcionar. Podés abrir la carpeta del proyecto en Antigravity para continuar desarrollándolo. Durante el uso, las partituras, el reconocimiento y la síntesis se procesan en tu equipo; los recursos de música, fuentes y sonidos están incluidos.

## Leer y escuchar una partitura

- Elegí uno de los nueve ritmos incluidos, o usá **Cargar Partitura** para abrir MusicXML (`.musicxml`, `.xml`, `.mxl`) o Guitar Pro (`.gp`, `.gp3`, `.gp4`, `.gp5`, `.gpx`).
- Si el archivo tiene varias pistas, el selector **Pista** prioriza las de percusión. Se escucha y exporta la pista seleccionada.
- Presioná **Reproducir**. El primer clic permite al navegador habilitar el audio.
- Ajustá el tempo con el deslizador, los botones, los multiplicadores o **TAP**. Se conservan las relaciones de tempo de los archivos que incluyen cambios de velocidad.
- Usá la línea de tiempo o los botones de compás para navegar. Activá el metrónomo y ajustá su volumen de forma independiente.

### Practicar en bucle

1. Ubicate en el compás inicial y pulsá **Punto A**: marca el inicio de ese compás.
2. Ubicate en el compás final y pulsá **Punto B**: incluye ese compás completo.
3. La sección se repite hasta desactivar **Bucle**. Si pulsás Bucle sin marcas, se repite el compás actual.

### Teclado y batería virtual

**Espacio** reproduce o pausa. Los accesos de batería son: **B** bombo; **S** caja; **X** aro; **H** charles cerrado; **O** abierto; **P** pedal; **T/G/F** toms alto/medio/base; **C** crash; **R** ride; **E** campana. También podés tocar los pads con el mouse o con pantalla táctil.

Los accesos no interfieren cuando escribís en un campo. El volumen general también afecta a los golpes manuales. Estos golpes manuales usan una síntesis Web Audio ligera; la reproducción de partituras y los WAV usan las muestras del SoundFont incluido.

## Leer una imagen y corregirla

1. Pulsá **Subir Imagen** y elegí PNG, JPG, WEBP o BMP (hasta 16 MB y 20 megapíxeles).
2. Indicá título, tempo, compás y subdivisión. El valor de BPM es **negras por minuto**, también en 6/8 y 12/8.
3. Al cambiar compás o subdivisión, pulsá **Analizar de nuevo**. Este botón vuelve a interpretar la imagen; reemplaza las correcciones que hayas hecho en la cuadrícula.
4. Revisá la imagen marcada y cada compás de la matriz. Pulsá una casilla para agregar o quitar un golpe. **Copiar compás anterior** ayuda con las repeticiones que aparecen con símbolos.
5. Pulsá **Cargar y guardar partitura**. La versión corregida queda en Mis partituras. Luego presioná **Reproducir**.
6. Podés reabrir la partitura guardada y usar **Editar notas** para seguir corrigiéndola.

La cuadrícula admite compases con denominador 4 u 8, corcheas, semicorcheas, fusas y subdivisiones de tresillo compatibles. El compás y la subdivisión se aplican a toda la imagen. Las partituras digitales sí conservan los cambios de compás y las figuras que admite alphaTab.

### Alcance del lector de imágenes

El reconocimiento es **asistido**: usa la posición de las cabezas de nota y una cuadrícula rítmica elegida por vos. Funciona mejor con cinco líneas horizontales, imágenes nítidas y la distribución habitual de batería. Corrige pequeñas inclinaciones; las pruebas incluidas cubren hasta ±5°.

Revisá siempre el resultado. Una foto con perspectiva o sombras, una distribución distinta de instrumentos, ritmos desigualmente espaciados, ligaduras, adornos, fusas mezcladas, polirritmias, silencios o signos de repetición pueden necesitar corrección. No calcula una tasa de exactitud para partituras reales desconocidas.

El programa no lee automáticamente títulos manuscritos, el tempo ni el compás impreso. No inventa un pentagrama cuando no puede encontrarlo y no sustituye silencios por un patrón anterior. Si una imagen no se distingue, probá una captura mejor o la partitura digital original.

## Guardar y recuperar

- Usá **Nombre** y **Guardar** para conservar una partitura importada o un ritmo de ejemplo, junto con el tempo y los ajustes de mezcla actuales.
- Las partituras escaneadas se guardan al cargarlas desde el editor.
- Elegí una entrada de **Mis partituras** para abrirla. El mismo navegador intenta recuperar la última partitura guardada al iniciar.
- **Descargar partitura** descarga el archivo musical actual. Para escaneos, es MusicXML editable; para archivos digitales, conserva el formato original.
- Los datos se guardan en `data/scores/` dentro de la carpeta de la aplicación. Conservá esa carpeta cuando actualices el programa o hagas una copia de seguridad. Un cambio de puerto no borra la colección, aunque pueda requerir seleccionar de nuevo la última entrada.

## Exportar WAV

1. Elegí el tempo y la pista.
2. Pulsá **Exportar WAV**. Podés incluir el metrónomo o limitar la salida al bucle A-B activo.
3. Pulsá **Comenzar Exportación**. Podés cancelarla mientras se genera.
4. Escuchá la vista previa y pulsá **Descargar WAV**.

El audio es estéreo PCM de 16 bits a 44.100 Hz. La velocidad cambia sin alterar los tonos de los instrumentos. Los WAV se generan por bloques para mantener la interfaz disponible; el límite de salida es 256 MiB por exportación.

## Verificación y mantenimiento

- `python test_system.py`: reconocimiento, compases, MusicXML, API y guardado recuperado tras reiniciar el servidor.
- `node tests/test_audio.mjs`: importa los nueve ejemplos con alphaTab, verifica los números MIDI y sintetiza audio real con cambios de tempo, volumen, metrónomo y bucle. Requiere Node.js 20.19 o superior; Node no es necesario para usar la aplicación.
- `node tests/test_controls.mjs`: verifica la lógica de transporte, bucles, navegación y visualización con un DOM simulado. No es una prueba visual en navegador.

Ver **VALIDACION.md** para los resultados de esta entrega y **CAMBIOS.md** para el contexto técnico que podés compartir con Antigravity.
