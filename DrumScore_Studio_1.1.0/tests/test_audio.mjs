import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createOfflineRenderer, createScoreMidi, pcm16, wavHeader } from '../js/offlineAudio.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const a=createRequire(import.meta.url)('../assets/alphatab/alphaTab.min.js');
const font=new Uint8Array(fs.readFileSync(path.join(root,'assets/soundfont/sonivox.sf2')));
const load=file=>a.importer.ScoreLoader.loadScoreFromBytes(new Uint8Array(fs.readFileSync(path.join(root,file))));
let assertions=0;
const check=(value,message)=>{assert.ok(value,message); assertions++;};
const allNotes=midi=>midi.tracks.flatMap(t=>t.events).filter(e=>e instanceof a.midi.NoteOnEvent);

for(const file of fs.readdirSync(path.join(root,'assets/scores'))) {
    const score=load('assets/scores/'+file);
    const {midi}=createScoreMidi(a,score,new a.Settings());
    const notes=allNotes(midi);
    check(notes.length>0,`${file}: notes`);
    check(notes.every(n=>n.channel===9),`${file}: percussion channel`);
    // The expected MIDI pitch is encoded in the authored instrument ID, independent of alphaTab parsing.
    const xml=fs.readFileSync(path.join(root,'assets/scores',file),'utf8');
    for(const match of xml.matchAll(/<midi-instrument id="P1-I(\d+)">[\s\S]*?<midi-unpitched>(\d+)<\/midi-unpitched>/g))
        check(Number(match[2])===Number(match[1])+1,`${file}: correct MusicXML base`);
}
const score=load('assets/scores/rock_beat_4_4.musicxml');
const {midi}=createScoreMidi(a,score,new a.Settings());
assert.deepEqual(allNotes(midi).slice(0,2).map(n=>n.noteKey).sort((a,b)=>a-b),[36,42]); assertions++;

function render(speed=1,range={startTick:0,endTick:7680},options={}) {
    const {midi,transpositions}=createScoreMidi(a,score,new a.Settings(),speed);
    const renderer=createOfflineRenderer(a,midi,font,{playbackRange:range,...options},transpositions);
    let samples=0,peak=0,energy=0,chunks=0,first;
    try {
        while(true) {
            const chunk=renderer.render(200); if(!chunk) break;
            if(!first) first=chunk.samples.slice();
            samples+=chunk.samples.length;
            check(chunk.samples.every(Number.isFinite),'finite PCM chunk');
            for(const s of chunk.samples) { peak=Math.max(peak,Math.abs(s)); energy+=s*s; }
            if(++chunks>500) throw new Error('Exporter did not finish.');
        }
    } finally { renderer.destroy(); }
    return {seconds:samples/88200,peak,energy,first};
}
const normal=render(), slow=render(0.5), fast=render(2), later=render(1,{startTick:7680,endTick:11520});
check(Math.abs(normal.seconds-4)<0.01,'two bars, 120 bpm: four seconds');
check(Math.abs(slow.seconds-8)<0.01,'half tempo doubles duration');
check(Math.abs(fast.seconds-2)<0.01,'double tempo halves duration');
check(Math.abs(later.seconds-2)<0.01,'nonzero loop start exports only selected bar');
check(normal.peak>0.05 && normal.peak<1,'audible unclipped drums');
check(render(1,undefined,{masterVolume:0}).peak===0,'master mute');
check(render(1,undefined,{includeMetronome:true}).energy!==normal.energy,'metronome included');
check(score.tempo===120,'export never mutates live tempo');
const header=wavHeader(8);const view=new DataView(header.buffer);
check(new TextDecoder().decode(header.slice(0,4))==='RIFF','RIFF');
check(view.getUint16(22,true)===2 && view.getUint32(24,true)===44100 && view.getUint16(34,true)===16,'stereo PCM format');
assert.deepEqual(Array.from(new Int16Array(pcm16(new Float32Array([-2,-.5,.5,2])).buffer)),[-32768,-16384,16384,32767]); assertions++;

// Python-generated grids are imported by the actual alphaTab runtime.
for(const [meter,subdivision,beats] of [['6/8',8,3],['12/8',16,6],['3/4',12,3],['4/4',24,4],['4/4',32,4]]) {
    const script=`from score_grid import compile_grid\nn,d=map(int,'${meter}'.split('/'))\ng=[{'slots':[{'instruments':['kick'] if i==0 else []} for i in range(n*${subdivision}//d)]}]\nprint(compile_grid(g,{'meter':'${meter}','subdivision':${subdivision},'bpm':90})['musicXml'])`;
    const run=spawnSync(process.env.PYTHON || 'python',['-c',script],{cwd:root});
    assert.equal(run.status,0,run.stderr.toString());
    const imported=a.importer.ScoreLoader.loadScoreFromBytes(new Uint8Array(run.stdout));
    const {midi}=createScoreMidi(a,imported,new a.Settings());
    check(imported.masterBars[0].calculateDuration()===960*beats,`${meter} duration`);
    assert.deepEqual(allNotes(midi).map(e=>e.noteKey),[36]); assertions++;
}
console.log(JSON.stringify({result:'PASS',presets:9,wavSeconds:{normal:normal.seconds,halfTempo:slow.seconds,doubleTempo:fast.seconds,selectedBar:later.seconds},peak:normal.peak,assertions},null,2));
