// jsc test/batch.js -- listfile  -> one JSON line per file: {file, bpm, beats, slices:[{s,type,f?}]}
var jsthis = {}; function outlet() {} function post() {} function arrayfromargs(a) { return Array.prototype.slice.call(a); }
load("breakgen.js"); load("test/wav.js");
MAX_SLICES = 999;
if (arguments[1]) { var o = JSON.parse(arguments[1]); for (var k in o) { if (k in TW) TW[k] = o[k]; else TH[k] = o[k]; } }
var files = read(arguments[0]).split("\n").filter(function (l) { return l.length; });
files.forEach(function (f) {
  var w = readWav(f);
  var an = analyzeSignal(w.x, w.sr, bpmHintFromName(f.split("/").pop()));
  print(JSON.stringify({ file: f, bpm: an.bpm, beats: an.beats,
    slices: an.slices.map(function (s) { return { s: s.s, type: s.type, pos: s.pos, feat: s.feat, feat2: s.feat2 }; }) }));
});
