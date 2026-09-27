# Offline preview: render generated pattern with the same slice/choke logic as the Max voices.
import json, sys, wave, subprocess, numpy as np
def readwav(p):
    w = wave.open(p); n = w.getnframes(); ch = w.getnchannels(); sr = w.getframerate()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).reshape(-1, ch).astype(np.float32) / 32768
    return (a if ch == 2 else np.repeat(a, 2, 1)), sr
def render(src, style, bars, seed, bpm, out):
    J = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
    d = json.loads(subprocess.check_output([J, "test/run_test.js", "--", src, str(style), str(bars), str(seed)]))
    a, sr = readwav(src)
    spb = 60 / bpm
    y = np.zeros((int((bars * 4 * spb + 1) * sr), 2), np.float32)
    notes = d["notes"]
    for i, n in enumerate(notes):
        rev = n["pitch"] >= 84; idx = n["pitch"] - (84 if rev else 36)
        sl = d["slices"][idx]
        s0, s1 = int(sl["s"] * sr / 1000), int(sl["e"] * sr / 1000)
        seg = a[s0:s1].copy()
        t = int(n["t"] * spb * sr)
        nxt = int(notes[i + 1]["t"] * spb * sr) if i + 1 < len(notes) else len(y)
        seg = seg[: max(0, nxt - t)]            # choke
        if rev: seg = seg[::-1]
        L = len(seg)
        if L == 0: continue
        env = np.ones(L, np.float32); f = min(L, int(0.002 * sr)); g = min(L, int(0.004 * sr))
        env[:f] = np.linspace(0, 1, f); env[L - g:] *= np.linspace(1, 0, g)
        y[t:t + L] += seg * env[:, None] * (n["vel"] / 127) ** 1.5
    y /= max(1e-6, np.abs(y).max()) / 0.9
    w = wave.open(out, "w"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((y * 32767).astype(np.int16).tobytes()); w.close()
    roles = {}
    for n in notes: roles[n["role"]] = roles.get(n["role"], 0) + 1
    print(out, len(notes), "notes", roles)
if __name__ == "__main__":
    for style, bpm, name in [(0, 170, "jungle"), (1, 160, "juke"), (2, 90, "boombap"), (3, 134, "breaks")]:
        render("test/cw_amen01_175.wav", style, 8, 11, bpm, "test/preview_%s.wav" % name)
