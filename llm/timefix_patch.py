import os, re, sys
sys.path.insert(0, os.path.expanduser(os.environ.get("EXTRACTOR_DIR", "~/mega-extractor")))
import incident_extractor.postprocess as pp
import timefix

_orig = pp.resolve_datetime
_orig_loc = pp.normalize_location

VAGUE_LOC = {"somewhere", "unknown", "not specified", "unspecified", "not mentioned", "unclear", "not sure",
             "unsure", "na", "n a", "none", "somewhere in the building", "somewhere here"}


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


def _loc(loc):
    if loc and re.sub(r"[^a-z ]", " ", loc.lower()).strip() in VAGUE_LOC:
        return None
    return _orig_loc(loc)


pp.resolve_datetime = _patched
pp.normalize_location = _loc
print("[timefix_patch] resolver + vague-location patch applied")
