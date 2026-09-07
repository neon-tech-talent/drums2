// Controller integration tests with a small DOM double, not a browser render test.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import fs from 'node:fs';
const a=createRequire(import.meta.url)('../assets/alphatab/alphaTab.min.js');
const ids=[...fs.readFileSync(new URL('../index.html',import.meta.url),'utf8').matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
class Element {
    constructor(){this.handlers={};this.value='';this.attrs={};this.style={};this.disabled=false;this.classes=new Set();this.classList={add:x=>this.classes.add(x),remove:x=>this.classes.delete(x),contains:x=>this.classes.has(x),toggle:(x,on)=>on?this.classes.add(x):this.classes.delete(x)};}
    addEventListener(type,fn){(this.handlers[type] ||= []).push(fn);}
    setAttribute(key,value){this.attrs[key]=value;}
    emit(type,event={}){for(const fn of this.handlers[type]||[])fn({target:this,...event});}
    closest(){return null;}
}
const elements=new Map(ids.map(id=>[id,new Element()]));
const el=id=>{assert.ok(elements.has(id),`Missing HTML element: ${id}`);return elements.get(id);};
const keyHandlers=[];
globalThis.document={getElementById:el,querySelectorAll:()=>[],querySelector:()=>null};
globalThis.window={alphaTab:a,addEventListener:(type,fn)=>{if(type==='keydown')keyHandlers.push(fn);}};
const {DrumScoreStudio}=await import('../js/app.js');
const studio=Object.create(DrumScoreStudio.prototype);
const score=a.importer.ScoreLoader.loadScoreFromBytes(new Uint8Array(fs.readFileSync(new URL('../assets/scores/rock_beat_4_4.musicxml',import.meta.url))));
const {createScoreMidi}=await import('../js/offlineAudio.js');
const {lookup}=createScoreMidi(a,score,new a.Settings());
let plays=0;
studio.api={score,isReadyForPlayback:true,tickPosition:0,timePosition:0,playbackSpeed:1,playPause(){plays++;}};
studio.visualizer={setVolume(){}};
studio.occurrences=lookup.masterBars;
studio.originalBpm=120;studio.currentBpm=120;studio.baseDurationMs=16000;studio.isPlaying=false;studio.tapTimes=[];studio.trackIndices=[0];
studio.attachEvents();
studio.resetLoop();
el('btn-loop-a').emit('click');
studio.api.tickPosition=7680;
el('btn-loop-b').emit('click');
assert.deepEqual(studio.api.playbackRange,{startTick:0,endTick:11520});
assert.equal(studio.api.isLooping,true);
el('btn-loop-toggle').emit('click');
assert.equal(studio.api.isLooping,false);assert.equal(studio.api.playbackRange,null);
studio.api.tickPosition=7800;
el('btn-loop-toggle').emit('click');
assert.deepEqual(studio.api.playbackRange,{startTick:7680,endTick:11520});
studio.resetLoop();
studio.api.tickPosition=8000;studio.jumpMeasure(-1);assert.equal(studio.api.tickPosition,3840);
studio.api.tickPosition=lookup.masterBars.at(-1).end;studio.jumpMeasure(1);assert.equal(studio.api.tickPosition,lookup.masterBars.at(-1).start);
studio.setBpm(60);assert.equal(studio.api.playbackSpeed,0.5);assert.equal(studio.totalDurationMs,32000);
studio.originalBpm=280;studio.setBpm(30);assert.equal(studio.currentBpm,35);assert.equal(studio.api.playbackSpeed,0.125);
let prevented=false;
for(const fn of keyHandlers)fn({code:'Space',key:' ',target:new Element(),preventDefault(){prevented=true;}});
assert.equal(plays,1);assert.equal(prevented,true);
for(const fn of keyHandlers)fn({code:'Space',key:' ',target:{closest:()=>true},preventDefault(){}});
assert.equal(plays,1,'typing does not start playback');
const visualizerSource=fs.readFileSync(new URL('../js/drumKitVisualizer.js',import.meta.url),'utf8');
assert.ok(!visualizerSource.includes("' ': 'kick'"),'space is reserved for transport');
const events=()=>({handlers:[],on(fn){this.handlers.push(fn);},emit(arg){for(const fn of this.handlers)fn(arg);}});
for(const name of ['error','renderFinished','scoreLoaded','playerReady','midiLoaded','playerStateChanged','playerPositionChanged','midiEventsPlayed'])studio.api[name]=events();
studio.source={settings:{bpm:90}};studio.loadedScore=null;
studio.setupAlphaTabEvents();
studio.api.scoreLoaded.emit(score);assert.equal(studio.currentBpm,90);
studio.setBpm(150);studio.api.scoreLoaded.emit(score);assert.equal(studio.currentBpm,150,'track rerender preserves speed');
const hits=[];studio.visualizer.triggerMidiNote=n=>hits.push(n);
studio.api.midiEventsPlayed.emit({events:[{track:0,noteKey:36,noteVelocity:95},{track:0,noteKey:42,noteVelocity:95},{track:1,noteKey:38,noteVelocity:95}]});
assert.deepEqual(hits,[36,42],'only the selected percussion track animates');
console.log('PASS: A-B repetition, navigation, tempo, track rerender, transport shortcuts and MIDI visualization.');
