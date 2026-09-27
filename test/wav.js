function readWav(path) {
  var bytes = read(path, "binary");
  var dv = new DataView(bytes.buffer);
  var p = 12, fmt = null, data = null;
  while (p + 8 <= bytes.length) {
    var id = String.fromCharCode(bytes[p], bytes[p+1], bytes[p+2], bytes[p+3]), sz = dv.getUint32(p + 4, true);
    if (id === "fmt ") fmt = { ch: dv.getUint16(p + 10, true), sr: dv.getUint32(p + 12, true), bits: dv.getUint16(p + 22, true) };
    if (id === "data") data = { off: p + 8, sz: sz };
    p += 8 + sz + (sz & 1);
  }
  var n = Math.floor(data.sz / (fmt.ch * 2)), x = new Float32Array(n);
  for (var i = 0; i < n; i++) { var s = 0; for (var c = 0; c < fmt.ch; c++) s += dv.getInt16(data.off + (i * fmt.ch + c) * 2, true) / 32768; x[i] = s / fmt.ch; }
  return { x: x, sr: fmt.sr, ch: fmt.ch };
}
