#!/bin/bash
# Out-of-fold stage-1 probabilities for stage-2 training (4 folds), then retrain both stages.
set -e
cd "$(dirname "$0")/.."
cp breakgen.js $TMPDIR/breakgen.js.bak; cp model.json $TMPDIR/model_full.json; rm -f model2.json
python3 - <<'P'
import json
rows=[json.loads(l) for l in open("data/train_feats.jsonl")]
files=sorted({r["file"] for r in rows})
for k in range(4):
    fold=set(files[k::4])
    open("data/fold%d_train.jsonl"%k,"w").write("".join(json.dumps(r)+"\n" for r in rows if r["file"] not in fold))
    open("data/fold%d_files.txt"%k,"w").write("\n".join(sorted(fold)))
P
: > data/train_oof.jsonl
for k in 0 1 2 3; do
  python3 test/train.py data/fold${k}_train.jsonl data/test_feats.jsonl 32 1e-3 120 --out model.json >/dev/null 2>&1
  python3 test/inject_model.py >/dev/null
  mkdir -p data/fold$k; rm -f data/fold$k/*
  while read f; do ln -sf "$PWD/$f" data/fold$k/; ln -sf "$PWD/${f%.wav}.json" data/fold$k/; done < data/fold${k}_files.txt
  python3 test/evaluate.py data/fold$k --dump data/fold${k}_oof.jsonl >/dev/null 2>&1
  cat data/fold${k}_oof.jsonl >> data/train_oof.jsonl
done
cp $TMPDIR/model_full.json model.json
python3 test/train.py data/train_oof.jsonl data/test_feats.jsonl 16 1e-3 100 --key feat2 --out model2.json 2>/dev/null | tail -1
python3 test/inject_model.py
