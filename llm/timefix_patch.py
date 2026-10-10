import os, sys
sys.path.insert(0, os.path.expanduser(os.environ.get("EXTRACTOR_DIR", "~/mega-extractor")))
import incident_extractor.postprocess as pp
import timefix

_orig = pp.resolve_datetime

def _patched(raw, now=None):
    if isinstance(now, str):
        now = now[:19]
    elif getattr(now, "tzinfo", None) is not None:
        now = now.replace(tzinfo=None)
    if raw:
        r = _orig(timefix.normalize_spoken_time(raw), now)
        if r:
            return r
    return _orig(raw, now)

pp.resolve_datetime = _patched
print("[timefix_patch] resolver patched")
