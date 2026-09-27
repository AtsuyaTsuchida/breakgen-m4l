import sys, itertools, json
sys.path.insert(0, "test")
from evaluate import run, match
d = sys.argv[1]
for odf, med, add in itertools.product([1], [1.2, 1.3, 1.45], [0.01, 0.015, 0.02]):
    res = run(d, {"odf": odf, "med": med, "add": add})
    ngt = ndet = nm = 0
    for r in res:
        lab, gt, pairs = match(r); ngt += len(gt); ndet += len(r["slices"]); nm += len(pairs)
    R, P = nm / ngt, nm / ndet
    print("odf %d med %.1f add %.2f  R %.3f P %.3f F %.3f" % (odf, med, add, R, P, 2 * R * P / (R + P)), flush=True)
