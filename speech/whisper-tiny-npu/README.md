# Whisper-tiny encoder on Hexagon NPU (SM8650 / v75)

Flow: openai-whisper (patched, SDPA off) -> ONNX (opset 14, input x.1 [1,80,3000]) -> snpe-onnx-to-dlc -> snpe-dlc-quantize (w8a16, --htp_socs sm8650) -> snpe-net-run --use_dsp on QIDK.
Decoder: vendor whisper-decoder-tiny.tflite (uses Flex ops -> needs full TensorFlow / tensorflow-lite-select-tf-ops on Android).

## Result (25 LibriSpeech dummy clips, same clips used for calibration)
- Encoder cosine sim fp32-CPU vs w8a16-NPU: min 0.9883, mean 0.9902
- WER fp32 CPU 12.0% vs w8a16 NPU 11.2% (501 words; text normalisation counts Mr./MISTER as an error, so compare only the two)
- NPU-only run (no --enable_cpu_fallback) succeeded, so the graph runs fully on the DSP
- No valid latency numbers yet

## Container gotchas (qairt_container, Python 3.10, QAIRT 2.47)
- numpy==1.26.4 (numpy 2.x breaks torch 1.13), protobuf==3.20.3 (onnx needs builder), torch 1.13.1 for export
- tensorflow 2.10.1 is missing small deps; fix_tf.sh installs them with --no-deps
- datasets<=3.6.0 needs librosa for audio decode; we decode with soundfile (Audio(decode=False))
- container PyPI downloads can be very slow; download wheels in WSL and pip install --no-index --find-links /local/wheels
- adb is Windows-side: copy files under /mnt/c/qidk and use relative paths; add </dev/null to adb shell when pasting several commands
- device libs: lib/aarch64-android/*.so, lib/hexagon-v75/unsigned/*.so
