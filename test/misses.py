import sys, collections, json
sys.path.insert(0, "test")
from evaluate import run, match
res = run(sys.argv[1]); miss = collections.Counter(); tot = collections.Counter(); gaps = collections.Counter(); late = []
for r in res:
    lab, gt, pairs = match(r)
    got = {id(g) for _, g in pairs}
    for i, g in enumerate(gt):
        tot[g[1]] += 1
        if id(g) not in got:
            miss[g[1]] += 1
            prev = gt[i - 1][0] if i else -1
            gaps["%d" % min(9, int((g[0] - prev) * 1000 // 25))] += 1
            near = min([abs(s["s"] / 1000 - g[0]) for s in r["slices"]] + [9])
            late.append(near)
    # beyond 16 beats cap?
print("missed by class", {k: "%d/%d" % (miss[k], tot[k]) for k in tot})
print("gap to previous onset (x25ms) of missed", sorted(gaps.items()))
import numpy as np; late = np.array(late)
print("nearest detection for missed: <50ms %.0f%%  <100ms %.0f%%" % (100 * (late < 0.05).mean(), 100 * (late < 0.1).mean()))
