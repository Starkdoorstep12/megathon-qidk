import os, io
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import numpy as np
import soundfile as sf
from datasets import load_dataset, Audio
from whisper.whisper.audio import log_mel_spectrogram, pad_or_trim
ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")
ds = ds.cast_column("audio", Audio(decode=False))
os.makedirs("input_features", exist_ok=True)
with open("list.txt", "w") as lf:
    for i in range(25):
        rec = ds[i]["audio"]
        src = io.BytesIO(rec["bytes"]) if rec.get("bytes") else rec["path"]
        a, sr = sf.read(src, dtype="float32")
        assert sr == 16000, sr
        if a.ndim > 1:
            a = a.mean(axis=1)
        mel = log_mel_spectrogram(pad_or_trim(a)).numpy().astype(np.float32)[None]
        assert mel.shape == (1, 80, 3000), mel.shape
        x = np.ascontiguousarray(mel.transpose(0, 2, 1))
        x.tofile("input_features/inp_val_%d.raw" % i)
        lf.write("x.1:=input_features/inp_val_%d.raw\n" % i)
print("CALIB OK", x.shape, x.dtype, "min/max", float(x.min()), float(x.max()))
