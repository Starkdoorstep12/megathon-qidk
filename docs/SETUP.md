# QIDK setup notes (verified on our device)
- Device: SM8650 (Snapdragon 8 Gen 3), Android 14, Hexagon v75, Adreno 750, ~11.6 GB RAM
- adb from WSL: wrapper script `adb` -> /mnt/c/platform-tools/adb.exe (Windows adb server; WSL cannot reach it over TCP). Use `</dev/null` on adb shell calls in pasted blocks. Push needs Windows paths, e.g. adb push 'C:\qidk\file' /data/local/tmp/
- Python 3.10 env: `uv venv --python 3.10 ~/qidk-env`; `uv pip install qai-hub qai-hub-models`; `qai-hub configure --api_token <TOKEN>` (never commit token)
- QAIRT SDK 2.47.0.260601: https://softwarecenter.qualcomm.com/api/download/software/sdks/Qualcomm_AI_Runtime_Community/All/2.47.0.260601/v2.47.0.260601.zip
- LLM path: upstream llama.cpp Hexagon backend. Build: `./scripts/snapdragon/build.py --target adb` (needs docker, user in docker group). Package -> /data/local/tmp/llama.cpp
- Model: unsloth/Qwen3-4B-Instruct-2507-GGUF, file Qwen3-4B-Instruct-2507-Q4_0.gguf (AI Hub fetch does not serve this asset)
- Bench: `./scripts/snapdragon/run.py --target adb --devices HTP0 -- llama-bench -p 512 -n 64 -m /data/local/tmp/gguf/Qwen3-4B-Instruct-2507-Q4_0.gguf`
- Results (Qwen3-4B Q4_0): NPU pp512 640.6 t/s, tg64 18.1 t/s; GPU pp512 119.5 t/s, tg64 11.4 t/s
- No prebuilt AI Hub NPU LLM bundle exists for 8 Gen 3; GenieX qairt runtime is not validated on this chip
