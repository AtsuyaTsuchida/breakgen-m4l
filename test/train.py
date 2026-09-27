#!/usr/bin/env python3
"""Train the slice classifier (1-hidden-layer MLP, numpy) and export weights to model.json.
python3 test/train.py data/train_feats.jsonl data/test_feats.jsonl [hidden]"""
import json, sys, numpy as np
C = "KSGH"
KEY = sys.argv[sys.argv.index("--key") + 1] if "--key" in sys.argv else "feat"
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "model.json"
def load(p):
    X, y = [], []
    for l in open(p):
        d = json.loads(l); X.append(d[KEY]); y.append(C.index(d["label"]))
    return np.array(X, np.float64), np.array(y)
Xtr, ytr = load(sys.argv[1]); Xte, yte = load(sys.argv[2])
H = int(sys.argv[3]) if len(sys.argv) > 3 else 24
lam = float(sys.argv[4]) if len(sys.argv) > 4 else 1e-3
EPOCHS = int(sys.argv[5]) if len(sys.argv) > 5 else 200
if "--val" in sys.argv:   # model selection on a held-out tail of the training set (test stays untouched)
    k = int(len(Xtr) * 0.85); Xte, yte = Xtr[k:], ytr[k:]; Xtr, ytr = Xtr[:k], ytr[:k]
mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
A, B = (Xtr - mu) / sd, (Xte - mu) / sd
rng = np.random.default_rng(0)
W1 = rng.normal(0, 1 / np.sqrt(A.shape[1]), (A.shape[1], H)); b1 = np.zeros(H)
W2 = rng.normal(0, 1 / np.sqrt(H), (H, 4)); b2 = np.zeros(4)
cw = len(ytr) / (4 * np.bincount(ytr, minlength=4))          # balance classes
params = [W1, b1, W2, b2]; m = [np.zeros_like(p) for p in params]; v = [np.zeros_like(p) for p in params]
def fwd(X):
    h = np.tanh(X @ W1 + b1); z = h @ W2 + b2; z -= z.max(1, keepdims=True)
    p = np.exp(z); p /= p.sum(1, keepdims=True); return h, p
lr = 0.01
for ep in range(1, EPOCHS + 1):
    idx = rng.permutation(len(A))
    for s in range(0, len(A), 128):
        bi = idx[s:s + 128]; X = A[bi]; Y = np.eye(4)[ytr[bi]]; wgt = cw[ytr[bi]][:, None]
        X = X + rng.normal(0, 0.05, X.shape)
        h, p = fwd(X)
        dz = (p - Y) * wgt / len(bi)
        gW2 = h.T @ dz + lam * W2; gb2 = dz.sum(0)
        dh = dz @ W2.T * (1 - h * h)
        gW1 = X.T @ dh + lam * W1; gb1 = dh.sum(0)
        for i, (pp, g) in enumerate(zip(params, [gW1, gb1, gW2, gb2])):
            m[i] = 0.9 * m[i] + 0.1 * g; v[i] = 0.999 * v[i] + 0.001 * g * g
            pp -= lr * m[i] / (np.sqrt(v[i]) + 1e-8)
    if ep % 50 == 0 or ep == EPOCHS:
        acc = lambda X, y: (fwd(X)[1].argmax(1) == y).mean()
        print("epoch %d train %.3f test %.3f" % (ep, acc(A, ytr), acc(B, yte)))
pred = fwd(B)[1].argmax(1)
print("gt\\pred " + " ".join("%5s" % c for c in C))
for a in range(4):
    row = [int(((yte == a) & (pred == b)).sum()) for b in range(4)]
    print("   %s    " % C[a] + " ".join("%5d" % x for x in row) + "  %5.1f%%" % (100 * row[a] / max(1, sum(row))))
if "--val" not in sys.argv:
  json.dump({"mu": mu.tolist(), "sd": sd.tolist(), "W1": W1.tolist(), "b1": b1.tolist(), "W2": W2.tolist(), "b2": b2.tolist()},
            open(OUT, "w"))
