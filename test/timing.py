import sys, numpy as np, json
sys.path.insert(0, "test")
from evaluate import run, match
d = sys.argv[1]
for th in [{"refine": 0}, {"refine": 1, "off": 256}, {"refine": 1, "off": 512}, {"refine": 1, "off": 768}]:
    res = run(d, th); errs = []; ngt = nm = ndet = 0
    for r in res:
        lab, gt, pairs = match(r, tol=0.05); ngt += len(gt); ndet += len(r["slices"])
        for sl, g in pairs: errs.append(sl["s"] / 1000 - g[0])
        nm += sum(1 for sl, g in pairs if abs(sl["s"] / 1000 - g[0]) <= 0.025)
    e = np.array(errs) * 1000
    print(th, "median err %.1fms  |err|<5ms %.0f%%  <10ms %.0f%%  R@25ms %.3f P %.3f" % (np.median(e), 100 * (abs(e) < 5).mean(), 100 * (abs(e) < 10).mean(), nm / ngt, nm / ndet))
