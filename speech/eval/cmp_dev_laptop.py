import json, os, re, sys
sys.path.insert(0, os.path.expanduser("~/megathon-qidk/speech/eval"))
import eval_server as e
dev = [l.split("HYP:", 1)[1].strip() for l in open(sys.argv[1]) if "HYP:" in l]
lap = json.load(open(sys.argv[2]))[sys.argv[3]]
refs = [l.strip() for l in open(sys.argv[4]) if l.strip()]
assert len(dev) == len(lap) == len(refs), (len(dev), len(lap), len(refs))
n = 0
for i, (d, l, r) in enumerate(zip(dev, lap, refs), 1):
    if e.norm(d) != e.norm(l):
        n += 1
        print("%02d REF: %s\n    DEV: %s\n    PC : %s" % (i, r, d, l))
print("\n%d of %d sentences differ between device and laptop" % (n, len(refs)))
