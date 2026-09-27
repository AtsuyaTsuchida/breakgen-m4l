var jsthis = {}; function outlet() {} function post() {} function arrayfromargs(a) { return Array.prototype.slice.call(a); }
load("breakgen.js"); load("test/wav.js");
var w = readWav(arguments[0]);
var sr=w.sr, x=w.x;
var an=analyzeSignal(x,sr,bpmHintFromName(arguments[0]));
// re-run classification on raw slices for features
var sl=an.slices.map(function(s){return {s:Math.round(s.s*sr/1000),e:Math.round(s.e*sr/1000),pos:s.pos}});
classifySlices(x,sr,sl);
sl.forEach(function(s){var f=s.f;print(s.pos.toFixed(2)+" "+s.type+" low="+f.low.toFixed(3)+" lmid="+f.lmid.toFixed(3)+" mid="+f.mid.toFixed(3)+" high="+f.high.toFixed(3)+" cen="+f.cen.toFixed(2)+" en="+f.en.toFixed(3))});
