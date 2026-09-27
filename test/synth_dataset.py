#!/usr/bin/env python3
"""Synthesise labelled breakbeats from Live's Core Library one-shots.

python3 test/synth_dataset.py OUTDIR N SPLIT(train|test) SEED
Writes OUTDIR/bNNN.wav + OUTDIR/bNNN.json ({"bpm", "beats", "onsets": [[sec, "K|S|G|H"], ...]}).
Samples are split by a hash of the file name so train and test never share a sound.
"""
import aifc, glob, json, os, random, sys, wave, zlib
import numpy as np

SR = 44100
CORE = "/Applications/Ableton Live 12 Suite.app/Contents/App-Resources/Core Library/Samples/One Shots/Drums"
JUKE = os.path.expanduser("~/Music/Ableton/User Library/Samples/JukeFootwork/Drums")


def read_audio(path):
    try:
        if path.lower().endswith((".aif", ".aiff")):
            f = aifc.open(path, "rb"); big = True
        else:
            f = wave.open(path, "rb"); big = False
        n, ch, sw, sr = f.getnframes(), f.getnchannels(), f.getsampwidth(), f.getframerate()
        raw = f.readframes(n); f.close()
    except Exception:
        return None
    if sw == 2:
        a = np.frombuffer(raw, ">i2" if big else "<i2").astype(np.float32) / 32768
    elif sw == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3)
        if big: b = b[:, ::-1]
        v = b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16)
        a = (np.where(v >= 1 << 23, v - (1 << 24), v) / float(1 << 23)).astype(np.float32)
    elif sw == 4:
        a = np.frombuffer(raw, ">i4" if big else "<i4").astype(np.float32) / 2 ** 31
    else:
        return None
    a = a.reshape(-1, ch).mean(1)
    if sr != SR:
        t = np.arange(int(len(a) * SR / sr)) * sr / SR
        a = np.interp(t, np.arange(len(a)), a).astype(np.float32)
    a = a[: int(SR * 1.2)]
    pk = np.abs(a).max()
    return a / pk if pk > 1e-4 else None


def pool(split):
    def ok(p):
        h = zlib.crc32(os.path.basename(p).encode()) % 4
        return (h != 0) if split == "train" else (h == 0)
    g = lambda d: [p for p in glob.glob(os.path.join(CORE, d, "*")) if p.lower().endswith((".wav", ".aif", ".aiff")) and ok(p)]
    P = {"K": g("Kick"), "S": g("Snare") + g("Clap") * 0, "C": g("Clap"), "H": [p for p in g("Hihat") if "open" not in p.lower()],
         "O": [p for p in g("Hihat") if "open" in p.lower()], "R": g("Ride")}
    if split == "train":
        P["K"] += [p for p in glob.glob(JUKE + "/Kick*.wav")]
        P["S"] += [p for p in glob.glob(JUKE + "/Snare*.wav")]
    return P


# 16-step templates (1 bar). K/S = main hits, g = ghost-snare candidates.
TEMPLATES = [
    {"K": [0, 2, 10, 11], "S": [4, 12], "g": [7, 9, 15]},          # amen-ish
    {"K": [0, 10], "S": [4, 12], "g": [7, 14]},                     # two-step
    {"K": [0, 7, 10], "S": [4, 12], "g": [9, 15]},                  # boom bap
    {"K": [0, 3, 6, 10, 14], "S": [8], "g": [5, 11, 15]},           # footwork
    {"K": [0, 8, 9], "S": [4, 12], "g": [6, 11, 15]},               # funky drummer-ish
    {"K": [0, 6, 10], "S": [4, 12], "g": [2, 7, 13, 15]},           # think-ish
    {"K": [0, 10, 13], "S": [4, 12], "g": [3, 9]},                  # apache-ish
    {"K": [0, 5, 8], "S": [4, 12, 14], "g": [10, 15]},
]


def fx_chain(y, rng):
    # vinyl / sampler / room colouring so the classifier doesn't learn clean one-shots only
    if rng.random() < 0.5:  # one-pole lowpass (dull vinyl)
        a = np.exp(-2 * np.pi * rng.uniform(3000, 11000) / SR)
        out = np.empty_like(y); s = 0.0
        # vectorised enough via lfilter-free recursion in chunks
        for i in range(len(y)):
            s = (1 - a) * y[i] + a * s; out[i] = s
        y = out
    if rng.random() < 0.4:  # highpass-ish thin break
        k = int(SR / rng.uniform(60, 180)); y = y - np.convolve(y, np.ones(k) / k, "same")
    if rng.random() < 0.6:  # saturation / bus compression
        d = rng.uniform(1.5, 5); y = np.tanh(y * d) / np.tanh(d)
    if rng.random() < 0.5:  # small room
        L = int(SR * rng.uniform(0.15, 0.6)); ir = rng.standard_normal(L).astype(np.float32) * np.exp(-np.arange(L) / (SR * rng.uniform(0.03, 0.15)))
        ir[0] = 1 / rng.uniform(0.05, 0.3)
        n = 1 << int(np.ceil(np.log2(len(y) + L)))
        y = np.fft.irfft(np.fft.rfft(y, n) * np.fft.rfft(ir, n), n)[: len(y)].astype(np.float32)
    if rng.random() < 0.5:  # bit-crush / sampler grit
        q = 2 ** rng.integers(8, 13); y = np.round(y * q) / q
    y = y + rng.standard_normal(len(y)).astype(np.float32) * rng.uniform(0, 0.004)
    return y / max(1e-6, np.abs(y).max()) * 0.9


def make_break(P, rng):
    bpm = float(rng.choice([rng.uniform(85, 100), rng.uniform(100, 140), rng.uniform(140, 178)]))
    bars = int(rng.choice([1, 2, 2, 4]))
    beats = bars * 4
    spb = 60 / bpm
    kit = {k: read_audio(rng.choice(v)) for k, v in P.items() if v}
    for k in list(kit):
        tries = 0
        while kit[k] is None and tries < 5:
            kit[k] = read_audio(rng.choice(P[k])); tries += 1
    snare = kit["C"] if rng.random() < 0.15 and kit.get("C") is not None else kit["S"]
    cym = "R" if rng.random() < 0.3 and kit.get("R") is not None else "H"
    swing = rng.uniform(0, 0.12) if rng.random() < 0.4 else 0.0
    L = int((beats * spb + 1.5) * SR)
    y = np.zeros(L, np.float32)
    events = {}  # step -> {"K": vel, "S": vel, "H": vel}
    for bar in range(bars):
        t = TEMPLATES[rng.integers(len(TEMPLATES))]
        for st in range(16):
            ev = {}
            if st in t["K"] and rng.random() < 0.92: ev["K"] = rng.uniform(0.75, 1.0)
            if st in t["S"] and rng.random() < 0.97: ev["S"] = rng.uniform(0.75, 1.0)
            if st in t["g"] and rng.random() < 0.6: ev["S"] = rng.uniform(0.12, 0.35)
            if rng.random() < 0.06 and "S" not in ev: ev["S"] = rng.uniform(0.12, 0.3)
            hat_rate = 2 if cym == "R" or rng.random() < 0.5 else 1
            if st % hat_rate == 0 and rng.random() < 0.9: ev["H"] = rng.uniform(0.25, 0.6) * (1.0 if st % 4 == 0 else 0.8)
            if ev: events[bar * 16 + st] = ev
    labels = []
    for step, ev in sorted(events.items()):
        tt = step * spb / 4
        if step % 2 == 1: tt += swing * spb / 4 * 2
        tt += rng.normal(0, 0.004)
        tt = max(0.0, tt) if step else 0.0
        i0 = int(tt * SR)
        for k, v in ev.items():
            s = {"K": kit["K"], "S": snare, "H": kit[cym] if not (k == "H" and step % 8 == 6 and kit.get("O") is not None and rng.random() < 0.3) else kit["O"]}[k]
            if s is None: continue
            g = v * {"K": 1.0, "S": 0.9, "H": 0.45}[k]
            seg = s[: L - i0] * g
            y[i0: i0 + len(seg)] += seg
        if "S" in ev and ev["S"] >= 0.5: lab = "S"
        elif "K" in ev: lab = "K"
        elif "S" in ev: lab = "G"
        else: lab = "H"
        labels.append([round(tt, 5), lab, sorted(ev)])
    y = y[: int(beats * spb * SR)]
    y = fx_chain(y, rng)
    return y, {"bpm": bpm, "beats": beats, "onsets": labels}


def write_wav(path, y):
    w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()


if __name__ == "__main__":
    out, n, split, seed = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
    os.makedirs(out, exist_ok=True)
    P = pool(split)
    rng = np.random.default_rng(seed)
    for i in range(n):
        y, lab = make_break(P, rng)
        bpm = int(round(lab["bpm"]))
        write_wav(os.path.join(out, "b%03d.wav" % i), y)
        json.dump(lab, open(os.path.join(out, "b%03d.json" % i), "w"))
    print(out, n, {k: len(v) for k, v in P.items()})
