import json
from server_backend import ServerBackend

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DAYS = ["unspecified", "today", "yesterday", "2_days_ago", "3_days_ago"] + WEEKDAYS
HOURS = [None] + list(range(24))
MINUTES = [None] + list(range(60))

INSTR = (
    "\n\nAlso fill time_parts from the time phrase you copied into datetime_raw. "
    "day: unspecified if no day is given; today; yesterday; 2_days_ago; 3_days_ago; or the weekday name for 'last friday'. "
    "hour: 24-hour clock (null if no clock time is given). minute: 0-59 (null if on the hour or not given). "
    "Examples: 'eight thirty this morning' -> day today, hour 8, minute 30; "
    "'yesterday evening around six' -> yesterday, 18, 0; "
    "'around half eight' -> unspecified, 8, 30; "
    "'last friday afternoon around three' -> friday, 15, 0; "
    "'this morning' -> today, null, null."
)


def with_time_parts(schema):
    s = json.loads(json.dumps(schema))
    s.setdefault("properties", {})["time_parts"] = {
        "type": "object",
        "properties": {"day": {"enum": DAYS}, "hour": {"enum": HOURS}, "minute": {"enum": MINUTES}},
        "required": ["day", "hour", "minute"],
        "additionalProperties": False,
    }
    s["required"] = list(s.get("required", [])) + ["time_parts"]
    return s


def convert(out):
    try:
        obj = json.loads(out)
    except Exception:
        return out
    if not isinstance(obj, dict):
        return out
    tp = obj.pop("time_parts", None)
    raw = obj.get("datetime_raw")
    if tp and raw and tp.get("hour") is not None:
        obj["datetime_raw"] = "@@C|%s|%d|%d|%s" % (tp.get("day", "unspecified"), tp["hour"], tp.get("minute") or 0, raw)
    return json.dumps(obj)


class TimePartsBackend(ServerBackend):
    def generate(self, messages, json_schema=None):
        if json_schema is None:
            return super().generate(messages, None)
        msgs = [dict(m) for m in messages]
        for m in msgs:
            if m["role"] == "system":
                m["content"] = m["content"] + INSTR
                break
        else:
            msgs.insert(0, {"role": "system", "content": INSTR.strip()})
        return convert(super().generate(msgs, with_time_parts(json_schema)))
