"""HTTP backend: calls llama-server (Hexagon NPU on the QIDK) via /completion with a
ChatML prompt rendered here, so the server's chat-template/thinking logic is bypassed.
Same messages + json_schema contract as incident_extractor.backend.LLMBackend."""
import json, os, time, urllib.request
from incident_extractor.backend import LLMBackend


def render_chatml(messages):
    parts = []
    for m in messages:
        parts.append("<|im_start|>%s\n%s<|im_end|>\n" % (m["role"], m["content"]))
    parts.append("<|im_start|>assistant\n")
    return "".join(parts)


class ServerBackend(LLMBackend):
    def __init__(self, base_url=None, max_tokens=400, temperature=0.0, timeout=180):
        self.base_url = (base_url or os.environ.get("LLM_URL") or "http://127.0.0.1:8081").rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.last_latency = None
        self.last_timings = None

    def generate(self, messages, json_schema=None):
        body = {
            "prompt": render_chatml(messages),
            "n_predict": self.max_tokens,
            "temperature": self.temperature,
            "cache_prompt": True,
            "stream": False,
            "stop": ["<|im_end|>"],
        }
        if json_schema is not None:
            body["json_schema"] = json_schema
        req = urllib.request.Request(
            self.base_url + "/completion",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        t0 = time.perf_counter()
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            resp = json.load(r)
        self.last_latency = time.perf_counter() - t0
        self.last_timings = resp.get("timings") or {}
        return resp["content"]
