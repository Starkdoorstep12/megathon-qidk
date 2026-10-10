import sys
from faster_whisper import WhisperModel
runs = [("tiny", "float32"), ("tiny", "int8"), ("tiny.en", "float32"), ("base.en", "float32"), ("small.en", "int8")]
for name, ct in runs:
    model = WhisperModel(name, device="cpu", compute_type=ct)
    segs, _ = model.transcribe(sys.argv[1], language="en", beam_size=1, temperature=0.0, condition_on_previous_text=False)
    print("%-9s %-8s %s" % (name, ct, " ".join(s.text.strip() for s in segs)), flush=True)
