import glob, os, sys, wave
from faster_whisper import WhisperModel
d = sys.argv[1]
files = sorted(glob.glob(os.path.join(d, "utt_*.wav")))
models = {n: WhisperModel(n, device="cpu", compute_type="int8") for n in ("small.en", "tiny")}
for i, f in enumerate(files, 1):
    with wave.open(f) as w:
        sec = w.getnframes() / w.getframerate()
    print("%02d  %4.1fs  %s" % (i, sec, os.path.basename(f)))
    for n, m in models.items():
        segs, _ = m.transcribe(f, language="en", beam_size=1, temperature=0.0, condition_on_previous_text=False)
        print("    %-8s %s" % (n, " ".join(s.text.strip() for s in segs)), flush=True)
