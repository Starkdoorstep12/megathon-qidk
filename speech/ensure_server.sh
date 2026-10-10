#!/bin/bash
# Makes sure the on-device whisper server is up and forwarded to localhost:8090. Safe to re-run.
cd /mnt/c/qidk || exit 1
if ! adb devices | tr -d "\r" | grep -q "device$"; then
  echo "NO DEVICE: replug USB, then: adb kill-server; adb start-server; adb devices"; exit 1
fi
adb forward tcp:8090 tcp:8090 </dev/null >/dev/null
if curl.exe -s -m 5 -o NUL http://127.0.0.1:8090/; then echo "server OK"; exit 0; fi
echo "server down -> restarting"
adb shell "pkill -9 whisper-server" </dev/null
sleep 1
timeout 8 adb shell "cd /data/local/tmp && setsid nohup ./wcpp/whisper-server -m wcpp/ggml-small.en-q5_1.bin -t 6 -l en -bs 1 --host 127.0.0.1 --port 8090 > wserver.log 2>&1 < /dev/null &" </dev/null
sleep 6
if curl.exe -s -m 5 -o NUL http://127.0.0.1:8090/; then echo "server OK"; else
  echo "STILL DOWN"; adb shell "tail -3 /data/local/tmp/wserver.log" </dev/null; exit 1; fi
