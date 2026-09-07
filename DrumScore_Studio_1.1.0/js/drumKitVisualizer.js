// drumKitVisualizer.js - Interactive Virtual Drum Kit Visualizer & Synthesizer
export class DrumKitVisualizer {
    constructor(containerElement) {
        this.container = containerElement;
        this.audioCtx = null;
        this.drumElements = new Map();
        this.keyBindings = {
            'b': 'kick',
            's': 'snare',
            'x': 'sidestick',
            'h': 'hihat-closed',
            'o': 'hihat-open',
            'p': 'hihat-pedal',
            't': 'tom-high',
            'g': 'tom-mid',
            'f': 'tom-floor',
            'c': 'crash',
            'r': 'ride',
            'e': 'ride-bell'
        };

        this.initAudio();
        this.render();
        this.attachEventListeners();
    }

    initAudio() {
        // Lightweight synthetic Web Audio fallback for direct pad clicks
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
            this.masterGain = this.audioCtx.createGain();
            this.masterGain.connect(this.audioCtx.destination);
        } catch (e) {
            console.warn('Web Audio API not supported on this browser', e);
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="drum-kit-container">
                <div class="drum-kit-header">
                    <div class="drum-kit-title">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <circle cx="12" cy="12" r="4"></circle>
                            <path d="M4.93 4.93l4.24 4.24"></path>
                            <path d="M14.83 14.83l4.24 4.24"></path>
                            <path d="M14.83 9.17l4.24-4.24"></path>
                            <path d="M4.93 19.07l4.24-4.24"></path>
                        </svg>
                        <span>Batería Virtual en Tiempo Real</span>
                    </div>
                    <div class="drum-kit-help">
                        <span>Haz clic en cualquier pieza o usa el teclado (B, S, H, O, T, G, F, C, R). Espacio: reproducir o pausar</span>
                    </div>
                </div>

                <div class="drum-stage" id="drum-stage">
                    <!-- Cymbals Top Row -->
                    <div class="drum-row cymbals-row">
                        <div class="drum-pad cymbal crash-cymbal" data-drum="crash" title="Crash Cymbal [C]">
                            <div class="cymbal-disc">
                                <div class="cymbal-bell"></div>
                            </div>
                            <span class="pad-label">Crash [C]</span>
                        </div>

                        <div class="drum-pad cymbal hihat-pad" data-drum="hihat-closed" title="Hi-Hat Cerrado [H] / Abierto [O]">
                            <div class="cymbal-disc hihat-disc">
                                <div class="cymbal-bell"></div>
                            </div>
                            <div class="hihat-labels">
                                <span class="pad-label">Hi-Hat [H]</span>
                                <span class="pad-sublabel" data-sub="open">Open [O]</span>
                            </div>
                        </div>

                        <div class="drum-pad cymbal ride-cymbal" data-drum="ride" title="Ride Cymbal [R] / Bell [E]">
                            <div class="cymbal-disc">
                                <div class="cymbal-bell ride-bell-highlight" data-sub="bell"></div>
                            </div>
                            <span class="pad-label">Ride [R]</span>
                        </div>
                    </div>

                    <!-- Toms Middle Row -->
                    <div class="drum-row toms-row">
                        <div class="drum-pad tom tom-high" data-drum="tom-high" title="High Tom [T]">
                            <div class="drum-head"><div class="drum-inner-ring"></div></div>
                            <span class="pad-label">Tom Alto [T]</span>
                        </div>

                        <div class="drum-pad tom tom-mid" data-drum="tom-mid" title="Mid Tom [G]">
                            <div class="drum-head"><div class="drum-inner-ring"></div></div>
                            <span class="pad-label">Tom Medio [G]</span>
                        </div>
                    </div>

                    <!-- Snare, Kick & Floor Tom Bottom Row -->
                    <div class="drum-row bottom-row">
                        <div class="drum-pad snare-pad" data-drum="snare" title="Tarola / Caja [S]">
                            <div class="drum-head snare-head">
                                <div class="drum-inner-ring"></div>
                                <div class="snare-rim" title="Side Stick [X]"></div>
                            </div>
                            <span class="pad-label">Caja [S]</span>
                        </div>

                        <div class="drum-pad kick-pad" data-drum="kick" title="Bombo [B]">
                            <div class="drum-head kick-head">
                                <div class="beater-dot"></div>
                                <div class="kick-pulse-ring"></div>
                            </div>
                            <span class="pad-label">Bombo [B]</span>
                        </div>

                        <div class="drum-pad tom tom-floor" data-drum="tom-floor" title="Floor Tom [F]">
                            <div class="drum-head floor-head"><div class="drum-inner-ring"></div></div>
                            <span class="pad-label">Tom Base [F]</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Cache drum pad DOM elements
        const pads = this.container.querySelectorAll('[data-drum]');
        pads.forEach(p => {
            this.drumElements.set(p.getAttribute('data-drum'), p);
        });
    }

    attachEventListeners() {
        // Click on pads to hit & hear
        this.drumElements.forEach((elem, key) => {
            elem.setAttribute('role', 'button');
            elem.setAttribute('tabindex', '0');
            elem.setAttribute('aria-label', elem.getAttribute('title'));
            elem.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                this.hit(key, true);
            });
            elem.addEventListener('keydown', e => {
                if ((e.key === 'Enter' || e.key === ' ') && !e.repeat) { e.preventDefault(); e.stopPropagation(); this.hit(key, true); }
            });
        });

        // Keyboard triggers
        window.addEventListener('keydown', (e) => {
            if (e.repeat || e.ctrlKey || e.metaKey || e.altKey || document.querySelector('.modal-backdrop.active') || e.target?.closest?.('input,select,textarea,button,[contenteditable="true"]')) {
                return;
            }
            const key = e.key.toLowerCase();
            if (this.keyBindings[key]) {
                const drumId = this.keyBindings[key];
                this.hit(drumId, true);
                if (key === ' ') {
                    e.preventDefault(); // prevent page scroll
                }
            }
        });
    }

    /**
     * Map General MIDI drum note number or articulation type to our visual pad id
     */
    triggerMidiNote(midiNumber, articulationName = '', playSound = false) {
        const name = (articulationName || '').toLowerCase();
        let drumId = null;

        // Note number mapping
        switch (Number(midiNumber)) {
            case 35: // Acoustic Bass Drum
            case 36: // Bass Drum 1
                drumId = 'kick';
                break;
            case 38: // Acoustic Snare
            case 40: // Electric Snare
                drumId = 'snare';
                break;
            case 37: // Side Stick
                drumId = 'sidestick';
                break;
            case 42: // Closed Hi-Hat
                drumId = 'hihat-closed';
                break;
            case 44: // Pedal Hi-Hat
                drumId = 'hihat-closed';
                break;
            case 46: // Open Hi-Hat
                drumId = 'hihat-open';
                break;
            case 41: // Low Floor Tom
            case 43: // High Floor Tom
                drumId = 'tom-floor';
                break;
            case 45: // Low Tom
            case 47: // Low-Mid Tom
                drumId = 'tom-mid';
                break;
            case 48: // Hi-Mid Tom
            case 50: // High Tom
                drumId = 'tom-high';
                break;
            case 49: // Crash Cymbal 1
            case 57: // Crash Cymbal 2
            case 55: // Splash
            case 52: // Chinese
                drumId = 'crash';
                break;
            case 51: // Ride Cymbal 1
            case 59: // Ride Cymbal 2
                drumId = 'ride';
                break;
            case 53: // Ride Bell
                drumId = 'ride';
                break;
            default:
                // Fallback by name inspection
                if (name.includes('kick') || name.includes('bass')) drumId = 'kick';
                else if (name.includes('snare')) drumId = 'snare';
                else if (name.includes('charley') || name.includes('hihat') || name.includes('hi-hat')) {
                    drumId = name.includes('open') ? 'hihat-open' : 'hihat-closed';
                }
                else if (name.includes('tom')) {
                    if (name.includes('high')) drumId = 'tom-high';
                    else if (name.includes('low') || name.includes('floor')) drumId = 'tom-floor';
                    else drumId = 'tom-mid';
                }
                else if (name.includes('ride')) drumId = 'ride';
                else if (name.includes('crash') || name.includes('splash') || name.includes('china')) drumId = 'crash';
                break;
        }

        if (drumId) {
            this.hit(drumId, playSound);
        }
    }

    /**
     * Trigger visual animation and optional synthesized preview sound
     */
    hit(drumId, playSound = false) {
        let element = this.drumElements.get(drumId);
        if (drumId === 'sidestick') element = this.drumElements.get('snare');
        if (drumId === 'ride-bell') element = this.drumElements.get('ride');
        if (drumId === 'hihat-pedal') element = this.drumElements.get('hihat-closed');
        if (!element && drumId === 'hihat-open') {
            element = this.drumElements.get('hihat-closed');
        }

        if (element) {
            element.classList.remove('hit');
            element.classList.remove('hit-open');
            // Trigger reflow to restart CSS animation
            void element.offsetWidth;
            if (drumId === 'hihat-open') {
                element.classList.add('hit-open');
            } else {
                element.classList.add('hit');
            }

            setTimeout(() => {
                element.classList.remove('hit');
                element.classList.remove('hit-open');
            }, 180);
        }

        if (playSound && this.audioCtx) {
            if (this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }
            this.playSyntheticSample(drumId);
        }
    }

    /**
     * High-quality Web Audio synthesized drum hits for instant tactile feedback
     */
    setVolume(value) {
        if (this.masterGain) this.masterGain.gain.value = Math.max(0, Math.min(1, value));
    }

    playSyntheticSample(drumId) {
        if (!this.audioCtx) return;
        const ctx = this.audioCtx;
        const now = ctx.currentTime;

        if (drumId === 'kick') {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(140, now);
            osc.frequency.exponentialRampToValueAtTime(38, now + 0.12);
            gain.gain.setValueAtTime(1.0, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
            osc.connect(gain);
            gain.connect(this.masterGain);
            osc.start(now);
            osc.stop(now + 0.36);
        } else if (drumId === 'sidestick') {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'triangle'; osc.frequency.setValueAtTime(900, now);
            gain.gain.setValueAtTime(0.5, now); gain.gain.exponentialRampToValueAtTime(0.001, now + 0.06);
            osc.connect(gain); gain.connect(this.masterGain); osc.start(now); osc.stop(now + 0.07);
        } else if (drumId === 'snare') {
            // Snare: Tone + Noise
            const osc = ctx.createOscillator();
            const toneGain = ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(180, now);
            osc.frequency.exponentialRampToValueAtTime(80, now + 0.1);
            toneGain.gain.setValueAtTime(0.7, now);
            toneGain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            osc.connect(toneGain);
            toneGain.connect(this.masterGain);
            osc.start(now);
            osc.stop(now + 0.15);

            // Noise buffer
            const bufferSize = ctx.sampleRate * 0.22;
            const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
            const output = buffer.getChannelData(0);
            for (let i = 0; i < bufferSize; i++) {
                output[i] = Math.random() * 2 - 1;
            }
            const whiteNoise = ctx.createBufferSource();
            whiteNoise.buffer = buffer;
            const filter = ctx.createBiquadFilter();
            filter.type = 'highpass';
            filter.frequency.setValueAtTime(1000, now);
            const noiseGain = ctx.createGain();
            noiseGain.gain.setValueAtTime(0.8, now);
            noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
            whiteNoise.connect(filter);
            filter.connect(noiseGain);
            noiseGain.connect(this.masterGain);
            whiteNoise.start(now);
        } else if (drumId === 'hihat-closed' || drumId === 'hihat-pedal') {
            this.playCymbalNoise(ctx, now, 7000, 0.05, 0.6);
        } else if (drumId === 'hihat-open') {
            this.playCymbalNoise(ctx, now, 6000, 0.45, 0.7);
        } else if (drumId === 'crash') {
            this.playCymbalNoise(ctx, now, 4500, 1.4, 0.85);
        } else if (drumId === 'ride' || drumId === 'ride-bell') {
            this.playCymbalNoise(ctx, now, 8500, 0.8, 0.5);
        } else if (drumId.startsWith('tom')) {
            const freq = drumId === 'tom-high' ? 180 : drumId === 'tom-mid' ? 130 : 90;
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now);
            osc.frequency.exponentialRampToValueAtTime(freq * 0.6, now + 0.25);
            gain.gain.setValueAtTime(0.9, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
            osc.connect(gain);
            gain.connect(this.masterGain);
            osc.start(now);
            osc.stop(now + 0.36);
        }
    }

    playCymbalNoise(ctx, now, highpassFreq, duration, volume) {
        const bufferSize = ctx.sampleRate * duration;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }
        const noise = ctx.createBufferSource();
        noise.buffer = buffer;
        const filter = ctx.createBiquadFilter();
        filter.type = 'highpass';
        filter.frequency.setValueAtTime(highpassFreq, now);
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(volume, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
        noise.connect(filter);
        filter.connect(gain);
        gain.connect(this.masterGain);
        noise.start(now);
    }
}
