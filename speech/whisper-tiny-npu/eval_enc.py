import os, re, glob
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import numpy as np
import tensorflow as tf
from datasets import load_dataset
from whisper.whisper.tokenizer import get_tokenizer

N = 25
EXP = 1500 * 384 * 4
def load(folder, i):
    fs = [f for f in glob.glob("/local/dev_out/%s/Result_%d/*.raw" % (folder, i)) if os.path.getsize(f) == EXP]
    assert len(fs) == 1, (folder, i, fs)
    return np.fromfile(fs[0], dtype=np.float32).reshape(1, 1500, 384)

def norm(s):
    return re.sub(r"[^a-z0-9' ]", "", s.lower()).split()
def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev, d[j] = d[j], cur
    return d[len(h)], len(r)

interp = tf.lite.Interpreter(model_path="openai-whisper/models/whisper-decoder-tiny.tflite")
ind = interp.get_input_details(); outd = interp.get_output_details()
print("decoder inputs:", [(x["shape"].tolist(), x["dtype"].__name__) for x in ind])
def decode(enc):
    toks = [50258, 50259, 50359, 50363]
    for _ in range(120):
        interp.resize_tensor_input(ind[1]["index"], [1, len(toks)])
        interp.allocate_tensors()
        interp.set_tensor(ind[0]["index"], enc.astype(ind[0]["dtype"]))
        interp.set_tensor(ind[1]["index"], np.array([toks], dtype=ind[1]["dtype"]))
        interp.invoke()
        out = interp.get_tensor(outd[0]["index"])
        nxt = int(np.argmax(out.reshape(-1, out.shape[-1])[-1]))
        if nxt == 50257:
            break
        toks.append(nxt)
    return toks[4:]

tok = get_tokenizer(multilingual=True)
refs = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")["text"][:N]
cos = []; ec = ed = nw = 0
for i in range(N):
    a = load("OUTPUT_32b_CPU", i); b = load("OUTPUT_DSP_W8A16", i)
    cos.append(float((a * b).sum() / (np.linalg.norm(a) * np.linalg.norm(b))))
    ta = tok.decode([t for t in decode(a) if t < 50257]).strip()
    tb = tok.decode([t for t in decode(b) if t < 50257]).strip()
    x, n = wer(refs[i], ta); y, _ = wer(refs[i], tb)
    ec += x; ed += y; nw += n
    if i < 3:
        print("REF :", refs[i]); print("CPU :", ta); print("NPU :", tb); print()
print("encoder cosine sim CPU vs NPU: min %.4f mean %.4f" % (min(cos), sum(cos) / len(cos)))
print("WER fp32 CPU: %.1f%%   WER w8a16 NPU: %.1f%%   (%d ref words)" % (100 * ec / nw, 100 * ed / nw, nw))
