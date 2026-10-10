import re, sys, os, json
W = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12}
NUM = "|".join(W)
MINS = {"fifteen":15,"twenty":20,"twenty five":25,"thirty":30,"forty":40,"forty five":45,"fifty":50,
        "oh five":5,"oh one":1,"oh two":2,"oh three":3,"oh four":4,"oh six":6,"oh seven":7,"oh eight":8,"oh nine":9,"ten":10}
MINRE = "|".join(sorted((m.replace(" ", r"[ -]?") for m in MINS), key=len, reverse=True))
FILL = r"\b(around|about|roughly|approximately|like|at|sort of|maybe|just after|just before)\b"

def _min(s):
    s = re.sub(r"[ -]+", " ", s.strip())
    return MINS[s]

def normalize_spoken_time(raw):
    s = re.sub(FILL, " ", raw.lower())
    s = re.sub(r"\ba (?=quarter|half)", "", s)
    mer = ""
    if re.search(r"\b(in the morning|this morning|morning)\b", s): mer = " am"
    elif re.search(r"\b(afternoon|evening|tonight|night)\b", s): mer = " pm"
    s = re.sub(r"\b(in the )?(this )?(morning|afternoon|evening)\b", " ", s)
    s = re.sub(r"\btonight\b", " ", s)
    def fmt(h, m): return " %d:%02d%s " % (h, m, mer)
    s = re.sub(r"\bhalf past (%s)\b" % NUM, lambda m: fmt(W[m.group(1)], 30), s)
    s = re.sub(r"\bhalf (%s)\b" % NUM, lambda m: fmt(W[m.group(1)], 30), s)
    s = re.sub(r"\bquarter past (%s)\b" % NUM, lambda m: fmt(W[m.group(1)], 15), s)
    s = re.sub(r"\bquarter (?:to|of) (%s)\b" % NUM,
               lambda m: fmt((W[m.group(1)] - 2) % 12 + 1, 45), s)
    s = re.sub(r"\b(%s) o'?clock\b" % NUM, lambda m: fmt(W[m.group(1)], 0), s)
    s = re.sub(r"\b(%s)[ -](%s)\b" % (NUM, MINRE), lambda m: fmt(W[m.group(1)], _min(m.group(2))), s)
    if not re.search(r"\d", s) and not re.search(r"\b(ago|hours?|minutes?|mins?|days?|weeks?)\b", s):  # bare hour
        s = re.sub(r"\b(%s)\b" % NUM, lambda m: fmt(W[m.group(1)], 0), s)
    return re.sub(r"\s+", " ", s).strip()

def resolve(raw, now):
    from incident_extractor.postprocess import resolve_datetime
    if isinstance(now, str):
        now = now[:19]  # drop tz offset: their resolver mixes aware 'now' with naive dateparser output
    return resolve_datetime(normalize_spoken_time(raw), now) or resolve_datetime(raw, now)

if __name__ == "__main__":
    ex = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/mega-extractor")
    sys.path.insert(0, ex)
    ok = tot = 0
    for line in open(os.path.join(ex, "data/testset.jsonl")):
        c = json.loads(line); e = c["expected"]
        if "datetime_iso" not in e: continue
        tot += 1
        got = resolve(e["datetime_raw"], c["now"])
        good = got is not None and got[:19] == e["datetime_iso"][:19]
        ok += good
        print("OK  " if good else "FAIL", c["id"], repr(e["datetime_raw"]), "->", normalize_spoken_time(e["datetime_raw"]), "->", got, "want", e["datetime_iso"])
    print("%d/%d" % (ok, tot))
