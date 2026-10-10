#!/bin/bash
# Starts the on-device whisper.cpp STT server and forwards port 8090 to the laptop.
# Needs /data/local/tmp/wcpp/{whisper-server,ggml-small.en-q5_1.bin} (built by build_whispercpp.sh).
adb shell "pkill whisper-server; cd /data/local/tmp && setsid nohup ./wcpp/whisper-server -m wcpp/ggml-small.en-q5_1.bin -t 6 -l en -bs 1 --host 127.0.0.1 --port 8090 > wserver.log 2>&1 < /dev/null &" </dev/null
sleep 3
adb shell "pgrep -l whisper-server" </dev/null
adb forward tcp:8090 tcp:8090 </dev/null
