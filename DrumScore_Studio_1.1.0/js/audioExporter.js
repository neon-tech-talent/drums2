import { createOfflineRenderer, createScoreMidi, pcm16, wavHeader } from './offlineAudio.js';

export class AudioExporter {
    static fontPromise = null;

    static async exportScoreToWav(api, options = {}, onProgress = () => {}) {
        if (!api?.score) throw new Error('Cargá una partitura antes de exportar.');
        const signal = options.signal;
        const checkCancelled = () => { if (signal?.aborted) throw new DOMException('Exportación cancelada', 'AbortError'); };
        checkCancelled();
        onProgress(2, 'Preparando los sonidos de batería…');
        const source = api.settings.player.soundFont;
        if (!this.fontPromise) {
            this.fontPromise = fetch(source).then(r => {
                if (!r.ok) throw new Error('No se pudo cargar el banco de sonidos.');
                return r.arrayBuffer();
            }).then(b => new Uint8Array(b)).catch(e => { this.fontPromise = null; throw e; });
        }
        const soundFont = await this.fontPromise;
        checkCancelled();
        const at = window.alphaTab;
        const speed = api.playbackSpeed || 1;
        const { midi, transpositions } = createScoreMidi(at, api.score, api.settings, speed);
        const sampleRate = 44100;
        const range = options.loopOnly ? api.playbackRange : null;
        if (options.loopOnly && (!range || range.endTick <= range.startTick)) throw new Error('Fijá un bucle A-B válido.');
        const channelVolumes = new Map();
        for (const track of api.score.tracks) {
            if (options.trackIndices && !options.trackIndices.includes(track.index)) {
                channelVolumes.set(track.playbackInfo.primaryChannel, 0);
                channelVolumes.set(track.playbackInfo.secondaryChannel, 0);
            }
        }
        const renderer = createOfflineRenderer(at, midi, soundFont,
            { ...options, sampleRate, playbackRange: range, channelVolumes }, transpositions);
        const chunks = [];
        let dataBytes = 0;
        try {
            while (true) {
                checkCancelled();
                const chunk = renderer.render(200);
                if (!chunk) break;
                const bytes = pcm16(chunk.samples);
                dataBytes += bytes.length;
                if (dataBytes > 256 * 1024 * 1024) throw new Error('El audio supera el tamaño disponible. Exportá un bucle más corto.');
                chunks.push(bytes);
                const fraction = range
                    ? (chunk.currentTick - range.startTick) / (range.endTick - range.startTick)
                    : chunk.currentTime / Math.max(1, chunk.endTime);
                onProgress(Math.min(95, Math.max(3, Math.round(3 + 92 * fraction))),
                    `Generando audio: ${(dataBytes / (sampleRate * 4)).toFixed(1)} s`);
                // Let the interface repaint and receive a cancel action between chunks.
                await new Promise(resolve => setTimeout(resolve, 0));
            }
        } finally { renderer.destroy(); }
        checkCancelled();
        if (!dataBytes) throw new Error('La partitura no generó audio.');
        const blob = new Blob([wavHeader(dataBytes, sampleRate), ...chunks], { type: 'audio/wav' });
        const title = (api.score.title || 'partitura').normalize('NFKD').replace(/[^a-z0-9_-]/gi, '_');
        const tempo = Math.round(api.score.tempo * speed);
        onProgress(100, 'Audio listo para escuchar y descargar.');
        return { blob, url: URL.createObjectURL(blob), filename: `${title}_${tempo}bpm${range ? '_bucle' : ''}.wav`, durationSeconds: dataBytes / (sampleRate * 4) };
    }

    static convertSamplesToWavBlob(chunks, sampleRate = 44100) {
        const pcm = chunks.map(pcm16);
        return new Blob([wavHeader(pcm.reduce((n, x) => n + x.length, 0), sampleRate), ...pcm], { type: 'audio/wav' });
    }

    static downloadWav(blob, filename) {
        const a = document.createElement('a');
        const url = URL.createObjectURL(blob);
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
}
