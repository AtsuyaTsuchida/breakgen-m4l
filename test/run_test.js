// jsc test/run_test.js -- <wav> <style> <bars> <seed>
var jsthis = {};
function outlet() {} function post() {} function arrayfromargs(a) { return Array.prototype.slice.call(a); }
load("breakgen.js");
var args = typeof scriptArgs !== "undefined" ? scriptArgs : arguments;
load("test/wav.js");
var w = readWav(args[0]), x = w.x, fmt = { sr: w.sr };
var name = args[0].split("/").pop();
var an = analyzeSignal(x, fmt.sr, bpmHintFromName(name));
var notes = generatePattern(an, parseInt(args[1] || "0"), {}, parseInt(args[2] || "4"), parseInt(args[3] || "1"));
print(JSON.stringify({ bpm: an.bpm, beats: an.beats, slices: an.slices, notes: notes }));
