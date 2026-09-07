// Uses the bundled alphaTab synthesizer with an offline output (no speakers).
export function createOfflineRenderer(alphaTab, midi, soundFont, options = {}, transpositions = new Map()) {
    const event = () => ({ on() {}, off() {} });
    const output = {
        sampleRate: options.sampleRate || 44100,
        ready: event(), sampleRequest: event(), samplesPlayed: event(),
        open() {}, activate() {}, play() {}, pause() {},
        resetSamples() {}, addSamples() {}, destroy() {}
    };
    const synth = new alphaTab.synth.AlphaSynth(output, 1000);
    const config = new alphaTab.synth.AudioExportOptions();
    config.sampleRate = output.sampleRate;
    config.soundFonts = [soundFont]; // Bytes, not the URL of the .sf2 file.
    config.masterVolume = options.masterVolume ?? 1;
    config.metronomeVolume = options.includeMetronome ? (options.metronomeVolume ?? 0.8) : 0;
    config.playbackRange = options.playbackRange || undefined;
    for (const [channel, volume] of options.channelVolumes || []) config.trackVolume.set(channel, volume);
    const renderer = synth.exportAudio(config, midi, [], transpositions);
    return { render: ms => renderer.render(ms), destroy: () => synth.destroy() };
}

export function createScoreMidi(alphaTab, score, settings, speed = 1) {
    const midi = new alphaTab.midi.MidiFile();
    const generator = new alphaTab.midi.MidiFileGenerator(
        score, settings, new alphaTab.midi.AlphaSynthMidiFileHandler(midi)
    );
    generator.generate();
    // Change event tempos, preserving pitches, repeats and tempo changes in the score.
    for (const track of midi.tracks) for (const event of track.events) {
        if (event instanceof alphaTab.midi.TempoChangeEvent) event.beatsPerMinute *= speed;
    }
    return { midi, transpositions: generator.transpositionPitches, lookup: generator.tickLookup };
}

export function pcm16(samples) {
    const bytes = new Uint8Array(samples.length * 2);
    const view = new DataView(bytes.buffer);
    for (let i = 0; i < samples.length; i++) {
        const s = Math.max(-1, Math.min(1, Number.isFinite(samples[i]) ? samples[i] : 0));
        view.setInt16(i * 2, Math.round(s * (s < 0 ? 32768 : 32767)), true);
    }
    return bytes;
}

export function wavHeader(dataBytes, sampleRate = 44100) {
    const bytes = new Uint8Array(44);
    const view = new DataView(bytes.buffer);
    const text = (at, s) => { for (let i = 0; i < s.length; i++) bytes[at + i] = s.charCodeAt(i); };
    text(0, 'RIFF'); view.setUint32(4, 36 + dataBytes, true); text(8, 'WAVE');
    text(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 2, true); view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 4, true); view.setUint16(32, 4, true); view.setUint16(34, 16, true);
    text(36, 'data'); view.setUint32(40, dataBytes, true);
    return bytes;
}
