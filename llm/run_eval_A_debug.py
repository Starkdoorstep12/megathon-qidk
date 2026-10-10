import os, sys, json, runpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timefix_patch
import eval as ev

_run = ev.run
LOG = []


def run2(*a, **k):
    r = _run(*a, **k)
    LOG.append({"missing": sorted(r.missing_mandatory), "raw": r.form.datetime_raw, "iso": r.form.datetime_iso,
                "loc": r.form.location, "desc": (r.form.description or "")[:50]})
    return r


ev.run = run2
sys.argv = ["run_eval_server.py"] + sys.argv[1:]
try:
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_eval_server.py"), run_name="__main__")
finally:
    ex = os.path.expanduser("~/mega-extractor/data/testset.jsonl")
    cases = [json.loads(l) for l in open(ex) if l.strip()]
    print("\n=== MISSING-FIELD DEBUG (only cases where got != expected) ===")
    for c, l in zip(cases, LOG):
        exp = sorted(c.get("expect_missing", []))
        if exp != l["missing"]:
            print(c["id"], "expected_missing=", exp, "got_missing=", l["missing"], "| raw=", repr(l["raw"]), "iso=", l["iso"], "| loc=", repr(l["loc"]), "| desc=", repr(l["desc"]))
