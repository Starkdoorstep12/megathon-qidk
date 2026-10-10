import os, sys, wave, argparse, subprocess
import numpy as np


def read(path):
    with wave.open(path, "rb") as w:
        return w.getframerate(), w.getnchannels(), w.getsampwidth(), w.readframes(w.getnframes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/mnt/c/qidk/qidk_rec/cache")
    ap.add_argument("--first", type=int, default=0)
    ap.add_argument("--last", type=int, default=7)
    ap.add_argument("--models", default="tiny,tiny.en,base.en,small.en")
    ap.add_argument("--no-models", action="store_true")
    a = ap.parse_args()
    idx = list(range(a.first, a.last + 1))
    paths = [os.path.join(a.dir, "android_record_%d.wav" % i) for i in idx]
    rate = ch = sw = None
    pcm = []
    print("chunk  rate  ch  bytes  seconds  rms(0-1)  peak(0-1)")
    for i, p in zip(idx, paths):
        r, c, s, data = read(p)
        rate, ch, sw = r, c, s
        x = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        pcm.append(data)
        print("%5d  %5d  %d  %6d  %6.2f    %.4f    %.3f" % (i, r, c, len(data), len(x) / float(r * c), float(np.sqrt((x ** 2).mean())), float(np.abs(x).max())))
    outdir = os.path.join(a.dir, "joined")
    os.makedirs(outdir, exist_ok=True)
    full = os.path.join(outdir, "full_%d_%d.wav" % (a.first, a.last))
    with wave.open(full, "wb") as w:
        w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(rate)
        w.writeframes(b"".join(pcm))
    print("\njoined file:", full, "(%.1f s)" % (sum(len(d) for d in pcm) / float(rate * ch * sw)))
    if a.no_models:
        return
    from faster_whisper import WhisperModel
    for m in a.models.split(","):
        model = WhisperModel(m, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(full, language="en", beam_size=1, vad_filter=False, condition_on_previous_text=False)
        whole = " ".join(s.text.strip() for s in segs)
        parts = []
        for p in paths:
            segs, _ = model.transcribe(p, language="en", beam_size=1, vad_filter=False, condition_on_previous_text=False)
            parts.append(" ".join(s.text.strip() for s in segs))
        print("\n[%s]" % m)
        print("  WHOLE (one pass)   :", whole)
        print("  PER-CHUNK (as app?):", " | ".join(parts))


if __name__ == "__main__":
    main()
