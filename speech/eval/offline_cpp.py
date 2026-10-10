#!/usr/bin/env python3
"""Offline sweep with whisper.cpp on the laptop: quantization x audio window x prompt.
Usage: python offline_cpp.py <clips_dir> <refs.txt>"""
import glob, json, math, os, subprocess, sys, time, wave, re
import jiwer
sys.path.insert(0, os.path.expanduser("~/megathon-qidk/speech/eval"))
import eval_server as e

BIN = os.environ.get("WCPP_BIN", os.path.expanduser("~/whisper.cpp/build-x86/bin/whisper-cli"))
MD = os.environ.get("WCPP_MODELS", "/mnt/c/qidk/wcpp")
PROMPT = ("Incident report. Rack, forklift, steam, burst, UPS, generator, boiler, hydraulic line, "
          "second floor, quarter to nine, half past midnight, eight thirty.")
CONFIGS = [  # label, model file, window ("dyn" = what the app does, "full" = 30 s), prompt
    ("q5_1  dyn-window", "ggml-small.en-q5_1.bin", "dyn", None),
    ("q5_1  full-window", "ggml-small.en-q5_1.bin", "full", None),
    ("q8_0  dyn-window", "ggml-small.en-q8_0.bin", "dyn", None),
    ("f16   full-window", "ggml-small.en.bin", "full", None),
    ("q5_1  dyn-window + prompt", "ggml-small.en-q5_1.bin", "dyn", PROMPT),
]

def run(model, window, prompt, files):
    out = []
    for f in files:
        _, sec = e.audio_ctx(f)
        cmd = [BIN, "-m", os.path.join(MD, model), "-f", f, "-t", "8", "-nt", "-np", "-bs", "1", "-l", "en"]
        ac = 0 if window == "full" else e.audio_ctx(f)[0]
        cmd += ["-ac", str(ac)]
        if prompt:
            cmd += ["--prompt", prompt]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise SystemExit("whisper-cli failed: " + r.stderr[-400:])
        out.append(re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", " ", r.stdout)).strip())
    return out

def main():
    files = sorted(glob.glob(os.path.join(sys.argv[1], "utt_*.wav")))
    refs = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    assert len(files) == len(refs), "need %d clips, got %d" % (len(refs), len(files))
    R = [e.norm(r) for r in refs]
    allhyp = {}
    for label, model, window, prompt in CONFIGS:
        if not os.path.exists(os.path.join(MD, model)):
            print("%-28s SKIPPED (missing %s)" % (label, model)); continue
        t0 = time.time()
        hyps = run(model, window, prompt, files)
        H = [e.norm(h) for h in hyps]
        exact = sum(a == b for a, b in zip(R, H))
        print("%-28s WER %5.1f%%  exact %2d/15  (%.0fs)" % (label, 100 * jiwer.wer(R, H), exact, time.time() - t0), flush=True)
        allhyp[label] = hyps
    json.dump(allhyp, open("offline_cpp_results.json", "w"), indent=1)

if __name__ == "__main__":
    main()
