import sys, itertools
sys.path.insert(0, "test")
from evaluate import run, match
d = sys.argv[1]
for med, add, gap, win in itertools.product([1.0, 1.1, 1.3], [0.005, 0.015, 0.03], [0.03, 0.045], [0.05, 0.1]):
    res = run(d, {"med": med, "mean": 1.0, "add": add, "gap": gap, "win": win})
    ngt = ndet = nm = 0
    for r in res:
        lab, gt, pairs = match(r); ngt += len(gt); ndet += len(r["slices"]); nm += len(pairs)
    R, P = nm / ngt, nm / ndet
    print("med %.1f add %.3f gap %.3f win %.2f  R %.3f P %.3f F %.3f" % (med, add, gap, win, R, P, 2 * R * P / (R + P)), flush=True)
