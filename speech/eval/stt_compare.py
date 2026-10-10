import os, re, sys, glob, json, time, subprocess, argparse
from num2words import num2words
import jiwer


def norm(t):
    t = t.lower().replace("&", " and ")
    t = re.sub(r"(\d)([a-z])", r"\1 \2", t)
    t = re.sub(r"([a-z])(\d)", r"\1 \2", t)
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b", lambda m: num2words(int(m.group(1))) + ("" if m.group(2) == "00" else " " + num2words(int(m.group(2)))), t)
    t = re.sub(r"\ba\.?m\.?\b", "am", t)
    t = re.sub(r"\bp\.?m\.?\b", "pm", t)
    t = re.sub(r"\d+", lambda m: num2words(int(m.group(0))), t)
    t = t.replace("-", " ")
    t = re.sub(r"[^a-z' ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rec", default="/mnt/c/qidk/rec")
    ap.add_argument("--refs", default=os.path.expanduser("~/megathon-qidk/speech/eval/refs.txt"))
    ap.add_argument("--models", default="tiny,tiny.en,base,base.en,small,small.en")
    ap.add_argument("--beam", type=int, default=1)
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    refs = [l.strip() for l in open(a.refs) if l.strip()]
    os.makedirs(os.path.join(a.rec, "wav"), exist_ok=True)
    wavs = []
    for i in range(len(refs)):
        src = glob.glob(os.path.join(a.rec, "%02d.*" % (i + 1)))
        if not src:
            print("MISSING recording for sentence %02d" % (i + 1)); wavs.append(None); continue
        out = os.path.join(a.rec, "wav", "%02d.wav" % (i + 1))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src[0], "-ac", "1", "-ar", "16000", out], check=True)
        wavs.append(out)
    results = {}
    for m in a.models.split(","):
        t0 = time.time()
        model = WhisperModel(m, device="cpu", compute_type="int8")
        hyps = []
        for w in wavs:
            if w is None:
                hyps.append(""); continue
            segs, _ = model.transcribe(w, language="en", beam_size=a.beam, vad_filter=False, condition_on_previous_text=False)
            hyps.append(" ".join(s.text.strip() for s in segs))
        pairs = [(norm(r), norm(h)) for r, h, w in zip(refs, hyps, wavs) if w is not None]
        wer = jiwer.wer([p[0] for p in pairs], [p[1] for p in pairs]) if pairs else float("nan")
        results[m] = {"wer": wer, "hyps": hyps, "secs": time.time() - t0}
        print("%-10s WER %.1f%%  (%d sentences, %.0fs)" % (m, wer * 100, len(pairs), time.time() - t0), flush=True)
    print("\n=== per-sentence (reference vs each model) ===")
    for i, r in enumerate(refs):
        if wavs[i] is None: continue
        print("\n%02d REF : %s" % (i + 1, r))
        for m in results:
            print("   %-9s: %s" % (m, results[m]["hyps"][i]))
    json.dump(results, open(os.path.join(a.rec, "stt_compare_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
