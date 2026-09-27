import sys, itertools, json
sys.path.insert(0, "test")
from evaluate import run
d = sys.argv[1]
labs = {}
rows = []
for back, prior, odd, kick in itertools.product([0.8, 1.5, 3.0], [0.3, 1.0, 2.0], [0, 0.6, 1.5], [0.3, 0.7, 1.5]):
    res = run(d, {"back": back, "prior": prior, "odd": odd, "kick": kick})
    ok = 0
    for r in res:
        if r["file"] not in labs: labs[r["file"]] = json.load(open(r["file"][:-4] + ".json"))["bpm"]
        ok += abs(r["bpm"] - labs[r["file"]]) / labs[r["file"]] < 0.02
    rows.append((ok / len(res), back, prior, odd, kick))
for r in sorted(rows)[-6:]: print("ok %.3f back %.1f prior %.1f odd %.1f kick %.1f" % r)
