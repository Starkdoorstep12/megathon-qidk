#!/usr/bin/env python3
"""Score the on-device whisper-server on fresh QIDK recordings.
Usage (from /mnt/c/qidk):  python eval_server.py uttrec refs.txt
Pairs utt_*.wav (sorted by name = recording order) with refs.txt lines in order."""
import glob, math, os, re, subprocess, sys, time, json, wave
import jiwer
from num2words import num2words

URL = "http://127.0.0.1:8090/inference"

def _time_words(m):
    h, mi = int(m.group(1)), int(m.group(2))
    if mi == 0:
        return num2words(h)
    if mi < 10:
        return "%s oh %s" % (num2words(h), num2words(mi))
    return "%s %s" % (num2words(h), num2words(mi))

def norm(t):
    t = t.lower().replace("-", " ")
    t = re.sub(r"\b(\d{1,2})[.:](\d{2})\b", _time_words, t)          # 8.30 / 8:30
    t = re.sub(r"\b(\d{1,2})(\d{2})\b", lambda m: _time_words(m) if int(m.group(1)) <= 12 and int(m.group(2)) < 60 else m.group(0), t)  # 830 / 1215
    t = re.sub(r"\d+", lambda m: num2words(int(m.group(0))), t)
    t = re.sub(r"[^a-z' ]", " ", t.replace("-", " "))
    return re.sub(r"\s+", " ", t).strip()

def audio_ctx(path):
    with wave.open(path) as w:
        sec = w.getnframes() / w.getframerate()
    return 0 if sec > 20 else min(1500, max(400, math.ceil(sec * 50) + 100)), sec

def transcribe(path):
    ac, sec = audio_ctx(path)
    t0 = time.time()
    if os.environ.get("FULL_CTX"):
        ac = 0
    cmd = ["curl.exe", "-sS", URL, "-F", "file=@" + path, "-F", "audio_ctx=%d" % ac,
           "-F", "temperature=0.0", "-F", "response_format=json"]
    if os.environ.get("PROMPT"):
        cmd += ["-F", "prompt=" + os.environ["PROMPT"]]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
    if not out.strip():
        raise SystemExit("empty reply from server: run ensure_server.sh first")
    text = json.loads(out)["text"]
    s = re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", text)).strip()
    s = re.sub(r"^(.{15,}?)(?:\s+\1)+$", r"\1", s, flags=re.I)   # drop whole-utterance repeats
    return s, time.time() - t0, sec

def main():
    d, refs_path = sys.argv[1], sys.argv[2]
    refs = [l.strip() for l in open(refs_path) if l.strip()]
    files = sorted(glob.glob(os.path.join(d, "utt_*.wav")))
    n = min(len(files), len(refs))
    print("%d recordings, %d reference lines, scoring first %d in order\n" % (len(files), len(refs), n))
    R, H, times = [], [], []
    for i in range(n):
        hyp, dt, sec = transcribe(files[i])
        R.append(norm(refs[i])); H.append(norm(hyp)); times.append((dt, sec))
        w = jiwer.wer(R[-1], H[-1]) if R[-1] else float("nan")
        print("%02d  WER %5.1f%%  %.1fs for %.1fs audio" % (i + 1, 100 * w, dt, sec))
        print("    REF:", refs[i]); print("    HYP:", hyp)
    print("\nOVERALL WER %.1f%% over %d sentences; mean latency %.2fs" % (
        100 * jiwer.wer(R, H), n, sum(t for t, _ in times) / n))

if __name__ == "__main__":
    main()
