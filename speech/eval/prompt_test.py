import glob, sys, jiwer
sys.path.insert(0, sys.argv[3] if len(sys.argv) > 3 else ".")
import eval_server as e
from faster_whisper import WhisperModel
files = sorted(glob.glob(sys.argv[1] + "/utt_*.wav"))
refs = [l.strip() for l in open(sys.argv[2]) if l.strip()]
assert len(files) == len(refs), "need %d files, got %d" % (len(refs), len(files))
PROMPTS = {
  "none": None,
  "vocab": "Incident report. Rack, forklift, steam, burst, UPS, generator, boiler, hydraulic line, second floor, quarter to nine, half past midnight, eight thirty.",
}
m = WhisperModel("small.en", device="cpu", compute_type="int8")
for name, p in PROMPTS.items():
    R, H = [], []
    for f, r in zip(files, refs):
        segs, _ = m.transcribe(f, language="en", beam_size=1, temperature=0.0, condition_on_previous_text=False, initial_prompt=p)
        h = " ".join(s.text.strip() for s in segs)
        R.append(e.norm(r)); H.append(e.norm(h))
        if name != "none" and jiwer.wer(e.norm(r), e.norm(h)) > 0: print("  ", h)
    print("== prompt=%-6s WER %.1f%%  exact %d/15" % (name, 100 * jiwer.wer(R, H), sum(a == b for a, b in zip(R, H))), flush=True)
