import os, sys, runpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timefix_patch  # baseline resolver fixes + extractor path
import incident_extractor.postprocess as pp
import server_backend as sb
import time_parts_backend as tpb
from c_resolver import resolve_parts

_prev = pp.resolve_datetime


def _c(raw, now=None):
    if raw and raw.startswith("@@C|"):
        _, day, h, m, orig = raw.split("|", 4)
        try:
            return resolve_parts(day, int(h), int(m), now)
        except Exception:
            return _prev(orig, now)
    return _prev(raw, now)


pp.resolve_datetime = _c
sb.ServerBackend = tpb.TimePartsBackend
sys.argv = ["run_eval_server.py"] + sys.argv[1:]
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_eval_server.py"), run_name="__main__")
