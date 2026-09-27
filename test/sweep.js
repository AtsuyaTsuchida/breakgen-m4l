var jsthis = {}; function outlet() {} function post() {} function arrayfromargs(a) { return Array.prototype.slice.call(a); }
load("breakgen.js"); load("test/wav.js");
var w = readWav(arguments[0]);
[[1.3,1.05,0.07],[1.2,1.0,0.04],[1.1,1.0,0.03],[1.0,1.0,0.02]].forEach(function(t){
  TH.med=t[0];TH.mean=t[1];TH.add=t[2];
  var an=analyzeSignal(w.x,w.sr,bpmHintFromName(arguments[0]));
  print(t.join(",")+" bpm="+an.bpm.toFixed(2)+" beats="+an.beats+" n="+an.slices.length+" :: "+an.slices.map(function(s){return s.pos.toFixed(2)+s.type}).join(" "));
});
