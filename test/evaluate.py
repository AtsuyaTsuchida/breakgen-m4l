#!/usr/bin/env python3
"""Score onset detection + K/S/G/H classification against synthetic labels.
python3 test/evaluate.py data/test [--dump feats.jsonl]"""
import glob, json, os, subprocess, sys, collections
J = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"
def run(d, th=None):
    wavs = sorted(glob.glob(os.path.join(d, "*.wav")))
    lst = os.path.join(os.environ.get("TMPDIR", "/tmp"), "bglist.txt"); open(lst, "w").write("\n".join(wavs))
    out = subprocess.check_output([J, "test/batch.js", "--", lst] + ([json.dumps(th)] if th else [])).decode().strip().split("\n")
    return [json.loads(l) for l in out]
def match(res, tol=0.025):
    lab = json.load(open(res["file"][:-4] + ".json"))
    gt = lab["onsets"]; used = set(); pairs = []
    for sl in res["slices"]:
        t = sl["s"] / 1000; best = None
        for i, g in enumerate(gt):
            if i in used: continue
            dt = abs(g[0] - t)
            if dt <= tol and (best is None or dt < best[0]): best = (dt, i)
        if best: used.add(best[1]); pairs.append((sl, gt[best[1]]))
    return lab, gt, pairs
if __name__ == "__main__":
    d = sys.argv[1]
    results = run(d)
    conf = collections.Counter(); ngt = ndet = nmatch = 0; bpm_ok = 0; dump = []
    for r in results:
        lab, gt, pairs = match(r)
        ngt += len(gt); ndet += len(r["slices"]); nmatch += len(pairs)
        bpm_ok += abs(r["bpm"] - lab["bpm"]) / lab["bpm"] < 0.02
        for sl, g in pairs:
            conf[(g[1], sl["type"])] += 1
            if "--dump" in sys.argv: dump.append({"file": r["file"], "feat": sl.get("feat"), "feat2": sl.get("feat2"), "pos": sl["pos"], "label": g[1], "pred": sl["type"]})
    correct = sum(v for (a, b), v in conf.items() if a == b)
    print("files %d  bpm-ok %.1f%%  onset recall %.1f%% precision %.1f%%" % (len(results), 100 * bpm_ok / len(results), 100 * nmatch / ngt, 100 * nmatch / max(1, ndet)))
    print("class acc (matched) %.1f%%   end-to-end (per GT onset) %.1f%%" % (100 * correct / max(1, nmatch), 100 * correct / ngt))
    C = "KSGH"
    print("gt\\pred " + " ".join("%5s" % c for c in C) + "  recall")
    for a in C:
        row = [conf[(a, b)] for b in C]; tot = sum(row)
        print("   %s    " % a + " ".join("%5d" % v for v in row) + "  %5.1f%%" % (100 * row[C.index(a)] / max(1, tot)))
    if "--dump" in sys.argv:
        with open(sys.argv[sys.argv.index("--dump") + 1], "w") as f:
            for x in dump: f.write(json.dumps(x) + "\n")
