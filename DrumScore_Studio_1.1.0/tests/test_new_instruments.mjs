import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createScoreMidi, createOfflineRenderer } from '../js/offlineAudio.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const a = createRequire(import.meta.url)('../assets/alphatab/alphaTab.min.js');
const font = new Uint8Array(fs.readFileSync(path.join(root, 'assets/soundfont/sonivox.sf2')));

const xml = `<?xml version="1.0" encoding="utf-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1">
      <part-name>Drums</part-name>
      <score-instrument id="P1-I36"><instrument-name>Bass Drum</instrument-name></score-instrument>
      <score-instrument id="P1-I53"><instrument-name>Ride Bell</instrument-name></score-instrument>
      <score-instrument id="P1-I52"><instrument-name>China Cymbal</instrument-name></score-instrument>
      <score-instrument id="P1-I55"><instrument-name>Splash Cymbal</instrument-name></score-instrument>
      <midi-instrument id="P1-I36"><midi-channel>10</midi-channel><midi-unpitched>37</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I53"><midi-channel>10</midi-channel><midi-unpitched>54</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I52"><midi-channel>10</midi-channel><midi-unpitched>53</midi-unpitched></midi-instrument>
      <midi-instrument id="P1-I55"><midi-channel>10</midi-channel><midi-unpitched>56</midi-unpitched></midi-instrument>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>24</divisions>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>percussion</sign></clef>
      </attributes>
      <!-- Chord: Kick + China -->
      <note>
        <unpitched><display-step>F</display-step><display-octave>4</display-octave></unpitched>
        <duration>24</duration><instrument id="P1-I36"/><voice>1</voice><type>quarter</type><stem>up</stem>
      </note>
      <note>
        <chord/>
        <unpitched><display-step>C</display-step><display-octave>6</display-octave></unpitched>
        <duration>24</duration><instrument id="P1-I52"/><voice>1</voice><type>quarter</type><stem>up</stem>
        <notehead>x</notehead>
      </note>
      <!-- Single: Ride Bell -->
      <note>
        <unpitched><display-step>F</display-step><display-octave>5</display-octave></unpitched>
        <duration>24</duration><instrument id="P1-I53"/><voice>1</voice><type>quarter</type><stem>up</stem>
        <notehead>diamond</notehead>
      </note>
      <!-- Single: Splash -->
      <note>
        <unpitched><display-step>B</display-step><display-octave>5</display-octave></unpitched>
        <duration>24</duration><instrument id="P1-I55"/><voice>1</voice><type>quarter</type><stem>up</stem>
        <notehead>x</notehead>
      </note>
      <!-- Rest -->
      <note>
        <rest/>
        <duration>24</duration><voice>1</voice><type>quarter</type>
      </note>
    </measure>
  </part>
</score-partwise>`;

const score = a.importer.ScoreLoader.loadScoreFromBytes(Buffer.from(xml));
const { midi, transpositions } = createScoreMidi(a, score, new a.Settings());
const notes = midi.tracks.flatMap(t => t.events).filter(e => e instanceof a.midi.NoteOnEvent);
console.log('Chord & Notes count:', notes.length);
console.log('Note keys played:', notes.map(n => n.noteKey));
assert.deepEqual(notes.map(n => n.noteKey), [36, 52, 53, 55]);

// Render audio with AlphaSynth
const renderer = createOfflineRenderer(a, midi, font, { playbackRange: { startTick: 0, endTick: 3840 } }, transpositions);
let peak = 0;
while (true) {
  const chunk = renderer.render(200);
  if (!chunk) break;
  for (const s of chunk.samples) peak = Math.max(peak, Math.abs(s));
}
renderer.destroy();
console.log('Audio render peak:', peak);
assert.ok(peak > 0.05, 'Audio was synthesized and audible with new instruments');
console.log('PASS: New instruments synthesize audio properly in AlphaSynth!');
