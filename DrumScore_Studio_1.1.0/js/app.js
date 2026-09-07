import { PRESETS } from './presets.js';
import { DrumKitVisualizer } from './drumKitVisualizer.js';
import { AudioExporter } from './audioExporter.js';
import { createScoreMidi } from './offlineAudio.js';

const DRUMS = [
    ['crash','Crash',49,'crash'], ['ride','Ride',51,'crash'],
    ['hihat','Charles cerrado',42,'hihat'], ['hihat_open','Charles abierto',46,'hihat'],
    ['hihat_pedal','Charles de pedal',44,'hihat'], ['tom_high','Tom alto',50,'tom'],
    ['tom_mid','Tom medio',47,'tom'], ['snare','Caja',38,'snare'],
    ['sidestick','Aro',37,'snare'], ['tom_low','Tom base',43,'tom'], ['kick','Bombo',36,'kick']
];
const $ = id => document.getElementById(id);
const copy = value => JSON.parse(JSON.stringify(value));
const clamp = (n, low, high) => Math.max(low, Math.min(high, n));
const formats = ['musicxml','xml','mxl','gp','gp3','gp4','gp5','gpx'];
const bytesToBase64 = bytes => {
    const parts = [];
    for (let i = 0; i < bytes.length; i += 32768) parts.push(String.fromCharCode(...bytes.subarray(i, i + 32768)));
    return btoa(parts.join(''));
};
const base64ToBytes = text => Uint8Array.from(atob(text), c => c.charCodeAt(0));
const formatTime = ms => {
    const seconds = Math.floor(Math.max(0, ms || 0) / 1000);
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2,'0')}`;
};
async function apiJson(path, data, signal) {
    const response = await fetch(path, data === undefined ? { signal } : {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data), signal
    });
    const result = await response.json();
    if (!response.ok || result.success === false) throw new Error(result.error || `Error ${response.status}`);
    return result;
}

export class DrumScoreStudio {
    constructor() {
        this.api = null;
        this.source = null;
        this.originalBpm = 120;
        this.currentBpm = 120;
        this.isPlaying = false;
        this.isLooping = false;
        this.loopStartTick = null;
        this.loopEndTick = null;
        this.totalDurationMs = 0;
        this.baseDurationMs = 0;
        this.occurrences = [];
        this.trackIndices = [];
        this.tapTimes = [];
        this.loadId = 0;
        this.saveChain = Promise.resolve();
        this.scannedGrid = [];
        this.scanConfig = { title:'Partitura de batería', bpm:120, meter:'4/4', subdivision:8 };
        this.visualizer = new DrumKitVisualizer($('drum-kit-visualizer-target'));
        this.attachEvents();
        this.populatePresets();
        this.initialize();
    }

    async initialize() {
        try {
            this.api = new window.alphaTab.AlphaTabApi($('alphaTab'), {
                core:{engine:'svg',fontDirectory:'assets/alphatab/font/',useWorkers:false,logLevel:'warning'},
                display:{staveProfile:'Default'},
                player:{enablePlayer:true,enableCursor:true,enableUserInteraction:true,soundFont:'assets/soundfont/sonivox.sf2'}
            });
            this.setupAlphaTabEvents();
            this.updateControls();
            await this.refreshSavedScores();
            let last;
            try { last = localStorage.getItem('drumscore.lastScore'); } catch {}
            if (last && Array.from($('saved-score-select').options).some(o => o.value === last)) await this.loadSaved(last);
            else await this.loadPreset(PRESETS[0].id);
        } catch (e) { this.showError(e); }
    }

    setupAlphaTabEvents() {
        this.api.error.on(e => this.showError(e));
        this.api.renderFinished.on(() => this.hideLoading());
        this.api.scoreLoaded.on(score => {
            if (this.loadedScore === score) return;
            this.loadedScore = score;
            this.originalBpm = score.tempo > 0 ? score.tempo : 120;
            this.setBpm(this.source?.settings?.bpm || this.originalBpm);
            this.resetLoop();
            this.updateControls();
        });
        this.api.playerReady.on(() => {
            this.setBpm(this.currentBpm);
            this.applyMix();
            this.updateControls();
        });
        this.api.midiLoaded.on(() => { this.applyMix(); this.updateControls(); });
        this.api.playerStateChanged.on(args => {
            this.isPlaying = args.state === 1;
            $('btn-play-pause').classList.toggle('playing', this.isPlaying);
            $('btn-play-pause').innerHTML = this.isPlaying ? '<span>Ⅱ Pausar</span>' : '<span>▶ Reproducir</span>';
            $('btn-play-pause').setAttribute('aria-label', this.isPlaying ? 'Pausar' : 'Reproducir');
        });
        this.api.playerPositionChanged.on(args => {
            this.totalDurationMs = args.endTime || this.baseDurationMs / (this.currentBpm/this.originalBpm);
            if (!this.scrubbing) this.updateTimeline(args.currentTime || 0);
            const occurrence = this.currentOccurrence(args.currentTick);
            if (occurrence) {
                const unit = 960 * 4 / occurrence.masterBar.timeSignatureDenominator;
                const beat = Math.floor((args.currentTick - occurrence.start) / unit) + 1;
                $('measure-display').textContent = `Compás: ${occurrence.masterBar.index + 1} | Tiempo: ${Math.max(1, beat)}`;
            }
        });
        // Actual audible events cover all voices, chords and percussion articulations.
        this.api.midiEventsPlayedFilter = [window.alphaTab.midi.MidiEventType.NoteOn];
        this.api.midiEventsPlayed.on(args => {
            for (const event of args.events) {
                if (event.noteVelocity > 0 && this.trackIndices.includes(event.track) && this.api.score?.tracks[event.track]?.staves.some(s=>s.isPercussion)) this.visualizer.triggerMidiNote(event.noteKey);
            }
        });
    }

    populatePresets() {
        $('preset-select').replaceChildren();
        const empty = new Option('Elegir un ritmo…', '');
        $('preset-select').add(empty);
        for (const preset of PRESETS) $('preset-select').add(new Option(`${preset.name} [${preset.bpm} BPM]`, preset.id));
    }

    async loadPreset(id) {
        const preset = PRESETS.find(p => p.id === id);
        if (!preset) return;
        const token = ++this.loadId;
        this.showLoading(`Cargando ${preset.name}…`);
        try {
            const r = await fetch(preset.file);
            if (!r.ok) throw new Error('No se pudo abrir el ritmo de ejemplo.');
            const data = new Uint8Array(await r.arrayBuffer());
            if (token !== this.loadId) return;
            this.loadBytes(data, {title:preset.name,filename:preset.file.split('/').pop(),presetId:id,description:preset.description});
            try { localStorage.removeItem('drumscore.lastScore'); } catch {}
        } catch (e) { if (token === this.loadId) this.showError(e); }
    }

    loadBytes(data, metadata) {
        // Parse before replacing the current session, so invalid files cannot erase it.
        const score = window.alphaTab.importer.ScoreLoader.loadScoreFromBytes(data, this.api.settings);
        if (!score.masterBars.length || !score.tracks.length) throw new Error('La partitura no contiene compases.');
        const { midi, lookup } = createScoreMidi(window.alphaTab, score, this.api.settings);
        this.occurrences = lookup.masterBars;
        const tempoEvents = midi.tracks.flatMap(t => t.events).filter(e => e instanceof window.alphaTab.midi.TempoChangeEvent).sort((a,b) => a.tick-b.tick);
        const end = this.occurrences.at(-1)?.end || 0;
        let ms = 0, tick = 0, tempo = 120;
        for (const event of tempoEvents) {
            ms += (event.tick-tick) / midi.division * 60000/tempo;
            tick = event.tick; tempo = event.beatsPerMinute;
        }
        this.baseDurationMs = ms + (end-tick) / midi.division * 60000/tempo;
        this.api.stop();
        this.source = {...metadata, data};
        const percussion = score.tracks.filter(t => t.staves.some(s => s.isPercussion));
        const candidates = percussion.length ? percussion : score.tracks;
        const savedTrack = metadata.settings?.trackIndex;
        const selected = candidates.find(t => t.index === savedTrack) || candidates[0];
        this.trackIndices = [selected.index];
        $('track-select').replaceChildren(...candidates.map(t => new Option(t.name || `Pista ${t.index+1}`, String(t.index))));
        $('track-select').value = String(selected.index);
        $('save-title').value = metadata.title || score.title || 'Partitura';
        $('preset-select').value = metadata.presetId || '';
        $('saved-score-select').value = metadata.id || '';
        $('preset-description').textContent = metadata.description || metadata.title || score.title;
        const settings = metadata.settings || {};
        if (Number.isFinite(settings.masterVolume)) $('master-volume').value = clamp(settings.masterVolume,0,1);
        if (Number.isFinite(settings.metronomeVolume)) $('metronome-volume').value = clamp(settings.metronomeVolume,0,1);
        if (typeof settings.metronome === 'boolean') $('metronome-toggle').checked = settings.metronome;
        $('library-status').textContent = metadata.id ? 'Partitura guardada en este equipo.' : 'Podés guardar esta partitura en Mis partituras.';
        $('app-error').hidden=true;
        this.api.renderScore(score, this.trackIndices);
        this.updateTimeline(0);
        this.updateControls();
    }

    async loadCustomFile(file) {
        const token = ++this.loadId;
        try {
            if (!formats.includes(file.name.split('.').pop().toLowerCase())) throw new Error('Usá un archivo MusicXML o Guitar Pro. Para fotos, elegí Escanear imagen.');
            if (!file.size || file.size > 16*1024*1024) throw new Error('La partitura debe pesar hasta 16 MB.');
            this.showLoading(`Abriendo ${file.name}…`);
            const data = new Uint8Array(await file.arrayBuffer());
            if (token !== this.loadId) return;
            this.loadBytes(data, { title:file.name.replace(/\.[^.]+$/, ''), filename:file.name });
            try { localStorage.removeItem('drumscore.lastScore'); } catch {}
        } catch(e) { if (token === this.loadId) this.showError(e); }
        finally { $('file-input').value = ''; }
    }

    async refreshSavedScores(selected = this.source?.id) {
        try {
            const { scores } = await apiJson('/api/scores');
            $('saved-score-select').replaceChildren(new Option('Mis partituras…', ''));
            for (const score of scores) $('saved-score-select').add(new Option(score.title,score.id));
            $('saved-score-select').value = selected || '';
        } catch(e) { $('library-status').textContent = e.message; }
    }

    async loadSaved(id) {
        if (!id) return;
        const token = ++this.loadId;
        this.showLoading('Abriendo partitura guardada…');
        try {
            const saved = await apiJson(`/api/scores/${id}`);
            if (token !== this.loadId) return;
            this.loadBytes(base64ToBytes(saved.data), saved);
            try { localStorage.setItem('drumscore.lastScore', id); } catch {}
        } catch(e) { if (token === this.loadId) this.showError(e); }
    }

    saveCurrent() {
        if (!this.source) return Promise.resolve();
        const source = this.source;
        const title = $('save-title').value.trim() || source.title;
        const settings = { bpm:this.currentBpm, masterVolume:Number($('master-volume').value),
            metronomeVolume:Number($('metronome-volume').value),metronome:$('metronome-toggle').checked,trackIndex:this.trackIndices[0] };
        $('library-status').textContent = 'Guardando…';
        this.saveChain = this.saveChain.catch(() => {}).then(async () => {
            const result = await apiJson('/api/scores', {
                id:source.id, title, filename:source.filename, data:bytesToBase64(source.data),
                grid:source.grid || null, config:source.config ? {...source.config,title} : null, settings
            });
            source.id = result.id; source.title = title; source.settings = settings;
            if (this.source === source) {
                $('library-status').textContent = 'Guardado. Podés cerrar y volver a abrir la aplicación.';
                try { localStorage.setItem('drumscore.lastScore',source.id); } catch {}
            }
            await this.refreshSavedScores();
        }).catch(e => { $('library-status').textContent = `No se pudo guardar: ${e.message}`; });
        return this.saveChain;
    }

    attachEvents() {
        const on = (id, type, fn) => $(id).addEventListener(type, fn);
        on('preset-select','change',e => this.loadPreset(e.target.value));
        on('saved-score-select','change',e => this.loadSaved(e.target.value));
        on('btn-save-score','click',() => this.saveCurrent());
        on('btn-edit-score','click',() => this.editSavedGrid());
        on('btn-download-score','click',() => {
            if (this.source) AudioExporter.downloadWav(new Blob([this.source.data]),this.source.filename);
        });
        on('track-select','change', e => {
            this.trackIndices = [Number(e.target.value)];
            this.api.renderTracks(this.api.score.tracks.filter(t => this.trackIndices.includes(t.index)));
            this.applyMix();
        });
        on('btn-play-pause','click',() => this.togglePlayPause());
        on('btn-stop','click',() => { this.api?.stop(); this.updateTimeline(0); });
        on('btn-rewind','click',() => { if (this.api) this.api.tickPosition = this.isLooping ? this.loopStartTick : 0; });
        on('btn-prev-measure','click',() => this.jumpMeasure(-1));
        on('btn-next-measure','click',() => this.jumpMeasure(1));
        on('timeline-scrubber','input',e => { this.scrubbing=true; this.updateTimeline(Number(e.target.value)*this.totalDurationMs/100); });
        on('timeline-scrubber','change',e => { if(this.api) this.api.timePosition=Number(e.target.value)*this.totalDurationMs/100; this.scrubbing=false; });
        on('bpm-slider','input',e => this.setBpm(Number(e.target.value)));
        on('btn-bpm-minus','click',() => this.setBpm(this.currentBpm-5));
        on('btn-bpm-plus','click',() => this.setBpm(this.currentBpm+5));
        on('btn-tap-tempo','click',() => this.tapTempo());
        document.querySelectorAll('.speed-pill').forEach(btn => btn.addEventListener('click',() => this.setBpm(this.originalBpm*Number(btn.dataset.speed))));
        for (const id of ['master-volume','metronome-volume']) on(id,'input',() => this.applyMix());
        on('metronome-toggle','change',() => this.applyMix());
        on('btn-loop-a','click',() => { this.loopStartTick=this.currentOccurrence()?.start ?? 0; this.updateLoop(); });
        on('btn-loop-b','click',() => { this.loopEndTick=this.currentOccurrence()?.end ?? null; this.updateLoop(); });
        on('btn-loop-toggle','click',() => this.toggleLoop());
        on('file-input','change',e => { if(e.target.files[0]) this.loadCustomFile(e.target.files[0]); });
        on('image-input','change',e => { if(e.target.files[0]) this.handleImageUpload(e.target.files[0]); e.target.value=''; });
        for (const type of ['dragenter','dragover','dragleave','drop']) on('drop-zone',type,e => {
            e.preventDefault(); $('drop-zone').classList.toggle('drag-active',type==='dragenter'||type==='dragover');
            if (type==='drop' && e.dataTransfer.files[0]) {
                const f=e.dataTransfer.files[0];
                if (/\.(png|jpe?g|webp|bmp)$/i.test(f.name)) this.handleImageUpload(f); else this.loadCustomFile(f);
            }
        });
        on('btn-close-scanner','click',() => this.closeScanner());
        on('btn-cancel-scan','click',() => this.closeScanner());
        on('btn-load-scanned-score','click',() => this.loadScannedScore());
        on('btn-reanalyze','click',() => { if(this.scanBlob) this.handleImageUpload(this.scanBlob,true); });
        on('btn-sample-rock','click',() => this.loadSampleImage('rock_beat_sample.png'));
        on('btn-sample-fill','click',() => this.loadSampleImage('tom_fill_sample.png'));
        on('matrix-measure','change',() => this.renderDrumMatrix());
        on('btn-copy-measure','click',() => {
            const i=Number($('matrix-measure').value);
            if (i>0) { this.scannedGrid[i].slots=copy(this.scannedGrid[i-1].slots); this.renderDrumMatrix(); this.updateStats(); }
        });
        on('btn-export-wav','click',() => this.openExport());
        on('btn-close-export','click',() => this.closeExport());
        on('btn-cancel-export','click',() => this.exportAbort?.abort());
        on('btn-start-export','click',() => this.performAudioExport());
        for (const id of ['scan-meter','scan-subdivision']) on(id,'change',() => {
            if(this.scanBlob) { $('btn-load-scanned-score').disabled=true; $('scanner-status-text').textContent='Pulsá Analizar de nuevo para aplicar el compás y la subdivisión elegidos.'; }
        });
        document.querySelectorAll('label.btn-upload-file').forEach(label => {
            label.tabIndex=0; label.setAttribute('role','button');
            label.addEventListener('keydown',e => {
                if(e.key==='Enter' || e.key===' ') { e.preventDefault(); e.stopPropagation(); label.querySelector('input').click(); }
            });
        });
        window.addEventListener('keydown',e => {
            const modal=document.querySelector('.modal-backdrop.active');
            if (modal) {
                if(e.key==='Escape') { this.closeScanner(); this.closeExport(); }
                if(e.key==='Tab') {
                    const list=Array.from(modal.querySelectorAll('button,input,select,audio')).filter(x=>!x.disabled && x.getClientRects().length);
                    const first=list[0], last=list.at(-1);
                    if(e.shiftKey && document.activeElement===first) { e.preventDefault(); last?.focus(); }
                    else if(!e.shiftKey && document.activeElement===last) { e.preventDefault(); first?.focus(); }
                }
                return;
            }
            if(e.repeat || e.ctrlKey || e.altKey || e.metaKey || e.target.closest?.('input,select,textarea,button,[contenteditable="true"]')) return;
            if(e.code==='Space') { e.preventDefault(); this.togglePlayPause(); }
        });
    }

    togglePlayPause() { if (this.api?.isReadyForPlayback) this.api.playPause(); }
    applyMix() {
        const volume = Number($('master-volume').value);
        this.visualizer.setVolume(volume);
        if (!this.api) return;
        this.api.masterVolume = volume;
        this.api.metronomeVolume = $('metronome-toggle').checked ? Number($('metronome-volume').value) : 0;
        if(this.api.score) for(const track of this.api.score.tracks) this.api.changeTrackMute([track], !this.trackIndices.includes(track.index));
    }
    setBpm(value) {
        if (!Number.isFinite(value)) return;
        const minimum=Math.max(30,Math.ceil(this.originalBpm*0.125));
        const maximum=Math.min(280,Math.floor(this.originalBpm*8));
        this.currentBpm=clamp(Math.round(value),minimum,maximum);
        $('bpm-slider').min=minimum; $('bpm-slider').max=maximum; $('bpm-slider').value=this.currentBpm;
        $('bpm-value').textContent=`${this.currentBpm} BPM`;
        const speed=this.currentBpm/this.originalBpm;
        if(this.api) this.api.playbackSpeed=speed;
        this.totalDurationMs=this.baseDurationMs/speed;
        document.querySelectorAll('.speed-pill').forEach(b=>b.classList.toggle('active',Math.abs(Number(b.dataset.speed)-speed)<0.015));
        if (!this.isPlaying) this.updateTimeline(this.api?.timePosition || 0);
    }
    tapTempo() {
        const now=performance.now();
        if(this.tapTimes.length && now-this.tapTimes.at(-1)>2000) this.tapTimes=[];
        this.tapTimes.push(now); this.tapTimes=this.tapTimes.slice(-5);
        if(this.tapTimes.length>1) this.setBpm(60000*(this.tapTimes.length-1)/(now-this.tapTimes[0]));
    }
    currentOccurrence(tick = this.api?.tickPosition || 0) {
        return this.occurrences.find(m=>tick>=m.start && tick<m.end) || this.occurrences.at(-1);
    }
    jumpMeasure(delta) {
        if(!this.api || !this.occurrences.length) return;
        const index=this.occurrences.indexOf(this.currentOccurrence());
        const next=this.occurrences[clamp(index+delta,0,this.occurrences.length-1)];
        this.api.tickPosition=next.start;
    }
    updateTimeline(currentMs) {
        const ms=clamp(currentMs || 0,0,this.totalDurationMs || 0);
        const percent=this.totalDurationMs>0 ? ms/this.totalDurationMs*100 : 0;
        $('timeline-progress').style.width=`${percent}%`;
        $('timeline-scrubber').value=percent;
        $('time-display').textContent=`${formatTime(ms)} / ${formatTime(this.totalDurationMs)}`;
    }
    resetLoop() {
        this.loopStartTick=null; this.loopEndTick=null; this.isLooping=false;
        if(this.api) { this.api.isLooping=false; this.api.playbackRange=null; }
        $('btn-loop-toggle').classList.remove('active');
        $('btn-loop-toggle').setAttribute('aria-pressed','false');
        $('loop-status').textContent='Sin bucle';
    }
    updateLoop() {
        if(this.loopStartTick===null || this.loopEndTick===null) {
            $('loop-status').textContent=this.loopStartTick!==null ? 'Inicio fijado. Elegí el compás final y pulsá Punto B.' : 'Fin fijado. Elegí el compás inicial y pulsá Punto A.';
            return;
        }
        const start=Math.min(this.loopStartTick,this.loopEndTick), end=Math.max(this.loopStartTick,this.loopEndTick);
        if(start===end) {
            this.api.isLooping=false; this.api.playbackRange=null; this.isLooping=false;
            $('btn-loop-toggle').classList.remove('active'); $('btn-loop-toggle').setAttribute('aria-pressed','false');
            $('loop-status').textContent='Elegí un final posterior al inicio.'; return;
        }
        this.loopStartTick=start; this.loopEndTick=end;
        this.api.playbackRange={startTick:start,endTick:end}; this.api.isLooping=true; this.isLooping=true;
        $('btn-loop-toggle').classList.add('active'); $('btn-loop-toggle').setAttribute('aria-pressed','true');
        $('loop-status').textContent=`Bucle: compás ${this.currentOccurrence(start).masterBar.index+1} al ${this.currentOccurrence(end-1).masterBar.index+1}`;
    }
    toggleLoop() {
        if(this.isLooping) return this.resetLoop();
        const m=this.currentOccurrence();
        if(m) { this.loopStartTick=m.start; this.loopEndTick=m.end; this.updateLoop(); }
    }
    updateControls() {
        const ready=Boolean(this.api?.isReadyForPlayback), loaded=Boolean(this.api?.score);
        for(const id of ['btn-play-pause','btn-stop','btn-rewind','btn-prev-measure','btn-next-measure','btn-loop-a','btn-loop-b','btn-loop-toggle','timeline-scrubber']) $(id).disabled=!ready;
        for(const id of ['btn-export-wav','btn-save-score','btn-download-score','track-select']) $(id).disabled=!loaded;
        $('btn-edit-score').disabled=!this.source?.grid;
    }

    readScanConfig() {
        return {title:$('scan-title').value || 'Partitura de batería',bpm:Number($('scan-bpm').value),
            meter:$('scan-meter').value,subdivision:Number($('scan-subdivision').value)};
    }
    setScanConfig(config) {
        this.scanConfig={...this.scanConfig,...config};
        $('scan-title').value=this.scanConfig.title; $('scan-bpm').value=this.scanConfig.bpm;
        $('scan-meter').value=this.scanConfig.meter; $('scan-subdivision').value=this.scanConfig.subdivision;
    }
    async handleImageUpload(blob, reanalyze=false) {
        this.scanAbort?.abort();
        const controller=new AbortController(); this.scanAbort=controller;
        this.scanBlob=blob;
        if(!reanalyze) { this.scanSourceId=null; this.setScanConfig({...this.readScanConfig(),title:blob.name?.replace(/\.[^.]+$/,'') || 'Partitura de batería'}); }
        this.openModal('image-scanner-modal');
        this.scannedGrid=[]; $('drum-grid-editor-wrap').style.display='none'; $('scanner-stats-row').style.display='none';
        $('btn-load-scanned-score').disabled=true; $('btn-reanalyze').disabled=true;
        $('scan-meter').disabled=false; $('scan-subdivision').disabled=false;
        document.querySelector('.scanner-spinner').style.display='block';
        $('scanner-status-text').textContent='Reconociendo pentagramas y notas…';
        try {
            if(!blob.size || blob.size>16*1024*1024) throw new Error('Usá una imagen de hasta 16 MB.');
            const bytes=new Uint8Array(await blob.arrayBuffer());
            if(controller.signal.aborted) return;
            const encoded=bytesToBase64(bytes);
            $('scanner-annotated-img').src=`data:${blob.type || 'image/png'};base64,${encoded}`;
            const result=await apiJson('/api/parse-image',{image:encoded,config:this.readScanConfig()},controller.signal);
            if(controller.signal.aborted) return;
            this.scannedGrid=result.grid; this.setScanConfig(result.config);
            $('scanner-annotated-img').src=result.annotatedImage;
            $('scanner-status-text').textContent=`${result.totalNotes} notas en ${result.measuresCount} compases. ${result.warnings.join(' ')}`;
            this.populateMatrix(); this.updateStats();
            $('btn-load-scanned-score').disabled=false;
        } catch(e) { if(e.name!=='AbortError') $('scanner-status-text').textContent=e.message; }
        finally {
            if(this.scanAbort===controller) { $('btn-reanalyze').disabled=false; document.querySelector('.scanner-spinner').style.display='none'; }
        }
    }
    async loadSampleImage(filename) {
        try {
            const response=await fetch(`assets/sample_images/${filename}`);
            if(!response.ok) throw new Error('No se pudo abrir la imagen de ejemplo.');
            this.setScanConfig({title:'Ejemplo de batería',meter:'4/4',subdivision:8,bpm:120});
            await this.handleImageUpload(await response.blob());
        } catch(e) { this.showError(e); }
    }
    populateMatrix() {
        $('matrix-measure').replaceChildren(...this.scannedGrid.map((m,i)=>new Option(`Compás ${i+1}`,String(i))));
        $('matrix-measure').value='0';
        $('drum-grid-editor-wrap').style.display='flex';
        this.renderDrumMatrix();
    }
    renderDrumMatrix() {
        const index=Number($('matrix-measure').value), measure=this.scannedGrid[index];
        if(!measure) return;
        const slots=measure.slots.length;
        const [numerator]=this.scanConfig.meter.split('/').map(Number);
        const perBeat=slots/numerator;
        const label=i=>`${Math.floor(i/perBeat)+1}${i%perBeat ? `·${Math.round(i%perBeat)+1}` : ''}`;
        let html='<table class="matrix-table"><thead><tr><th class="matrix-inst-col" scope="col">Instrumento</th>';
        for(let i=0;i<slots;i++) html+=`<th scope="col" class="beat-header ${i%perBeat===0?'beat-downbeat':''}">${label(i)}</th>`;
        html+='</tr></thead><tbody>';
        for(const [id,name,,style] of DRUMS) {
            html+=`<tr><th scope="row" class="matrix-inst-col">${name}</th>`;
            for(let i=0;i<slots;i++) {
                const active=measure.slots[i].instruments.includes(id);
                html+=`<td><button class="matrix-cell-btn ${active?'active '+style:''}" data-inst="${id}" data-slot="${i}" aria-pressed="${active}" aria-label="${name}, compás ${index+1}, posición ${label(i)}" title="${name}, ${label(i)}"></button></td>`;
            }
            html+='</tr>';
        }
        $('drum-matrix-container').innerHTML=html+'</tbody></table>';
        $('btn-copy-measure').disabled=index===0;
        $('drum-matrix-container').querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{
            const list=measure.slots[Number(btn.dataset.slot)].instruments;
            const found=list.indexOf(btn.dataset.inst);
            if(found>=0) list.splice(found,1);
            else {
                list.push(btn.dataset.inst);
                this.visualizer.triggerMidiNote(DRUMS.find(d=>d[0]===btn.dataset.inst)[2],'',true);
            }
            const drum=DRUMS.find(d=>d[0]===btn.dataset.inst);
            btn.classList.toggle('active',found<0); btn.classList.toggle(drum[3],found<0);
            btn.setAttribute('aria-pressed',String(found<0)); this.updateStats();
        }));
    }
    updateStats() {
        const counts={kick:0,snare:0,hihat:0,toms:0,cymbals:0};
        for(const m of this.scannedGrid) for(const s of m.slots) for(const id of s.instruments) {
            const category=id.startsWith('tom')?'toms':id.startsWith('hihat')?'hihat':id==='sidestick'?'snare':['crash','ride'].includes(id)?'cymbals':id;
            counts[category]++;
        }
        for(const [key,label] of [['kick','Bombos'],['snare','Cajas'],['hihat','Charles'],['toms','Toms'],['cymbals','Platos']]) $(`stat-${key}`).textContent=`${counts[key]} ${label}`;
        $('scanner-stats-row').style.display='flex';
    }
    editSavedGrid() {
        if(!this.source?.grid) return;
        this.scanAbort?.abort(); this.scanBlob=null; this.scanSourceId=this.source.id || null;
        this.scannedGrid=copy(this.source.grid);
        this.setScanConfig({...this.source.config,bpm:this.currentBpm,title:$('save-title').value});
        this.openModal('image-scanner-modal');
        $('scanner-annotated-img').removeAttribute('src');
        $('scanner-status-text').textContent='Editá los golpes y cargá la partitura para guardar los cambios.';
        document.querySelector('.scanner-spinner').style.display='none';
        $('btn-reanalyze').disabled=true; $('scan-meter').disabled=true; $('scan-subdivision').disabled=true;
        $('btn-load-scanned-score').disabled=false; this.populateMatrix(); this.updateStats();
    }
    async loadScannedScore() {
        $('btn-load-scanned-score').disabled=true;
        try {
            const result=await apiJson('/api/compile-grid',{grid:this.scannedGrid,config:this.readScanConfig()});
            const data=new TextEncoder().encode(result.musicXml);
            ++this.loadId;
            this.loadBytes(data,{id:this.scanSourceId,title:result.config.title,filename:'partitura_bateria.musicxml',
                grid:result.grid,config:result.config,settings:{bpm:result.config.bpm}});
            this.closeScanner();
            await this.saveCurrent();
        } catch(e) { $('scanner-status-text').textContent=e.message; $('btn-load-scanned-score').disabled=false; }
    }
    closeScanner() { this.scanAbort?.abort(); this.closeModal('image-scanner-modal'); }

    openExport() {
        if(!this.api?.score) return;
        this.openModal('export-modal');
        $('export-loop-only').disabled=!this.isLooping; $('export-loop-only').checked=false;
        $('export-status').textContent=`Exportar a ${this.currentBpm} BPM, WAV estéreo.`;
        $('export-progress').style.width='0%'; $('export-result').style.display='none';
        $('btn-download-export').style.display='none'; $('btn-start-export').style.display='inline-flex';
    }
    async performAudioExport() {
        if(this.exportAbort) return;
        const controller=new AbortController(); this.exportAbort=controller;
        $('btn-start-export').style.display='none'; $('btn-cancel-export').hidden=false;
        try {
            const result=await AudioExporter.exportScoreToWav(this.api,{
                signal:controller.signal,includeMetronome:$('export-include-metronome').checked,
                metronomeVolume:Number($('metronome-volume').value),masterVolume:Number($('master-volume').value),
                loopOnly:$('export-loop-only').checked,trackIndices:[...this.trackIndices]
            },(percent,message)=>{ $('export-progress').style.width=`${percent}%`; $('export-status').textContent=message; });
            if(this.exportUrl) URL.revokeObjectURL(this.exportUrl);
            this.exportUrl=result.url; $('export-audio-preview').src=result.url;
            $('export-result').style.display='block'; $('btn-download-export').style.display='inline-flex';
            $('btn-download-export').onclick=()=>AudioExporter.downloadWav(result.blob,result.filename);
        } catch(e) {
            $('export-status').textContent=e.name==='AbortError'?'Exportación cancelada.':e.message;
            $('btn-start-export').style.display='inline-flex';
        } finally { this.exportAbort=null; $('btn-cancel-export').hidden=true; }
    }
    closeExport() { this.exportAbort?.abort(); $('export-audio-preview').pause(); this.closeModal('export-modal'); }
    openModal(id) {
        if(!$(id).classList.contains('active')) this.previousFocus=document.activeElement;
        $(id).classList.add('active'); $(id).querySelector('button')?.focus();
    }
    closeModal(id) {
        if($(id).classList.contains('active')) { $(id).classList.remove('active'); this.previousFocus?.focus(); }
    }
    showLoading(message) { $('app-error').hidden=true; $('loading-text').textContent=message; $('loading-overlay').classList.remove('hidden'); }
    hideLoading() { $('loading-overlay').classList.add('hidden'); }
    showError(error) {
        console.error(error); this.hideLoading();
        $('app-error').textContent=`No se pudo completar la operación: ${error.message || error}`;
        $('app-error').hidden=false;
        this.updateControls();
    }
}

window.addEventListener('DOMContentLoaded',()=>{ window.drumStudio=new DrumScoreStudio(); });
