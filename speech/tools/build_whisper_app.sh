set -e
export ANDROID_HOME=$HOME/android-sdk
ROOT=$(sg docker -c 'docker exec qairt_container printenv QAIRT_SDK_ROOT' </dev/null | tr -d '\r')
echo "SDK root in container: [$ROOT]"
[ -n "$ROOT" ] || { echo "ERROR: QAIRT_SDK_ROOT is empty in the container"; exit 2; }
SD=$HOME/qairt_work/sdk_min
rm -rf "$SD"; mkdir -p "$SD/include" "$SD/lib/android"
sg docker -c "docker cp qairt_container:$ROOT/include/SNPE $SD/include/"
sg docker -c "docker cp qairt_container:$ROOT/lib/android/snpe-release.aar $SD/lib/android/"
ls "$SD/include/SNPE" | head -3
ls -la "$SD/lib/android"
cd "$HOME/qairt_work/NLPSolution3-AutomaticSpeechRecognition-Whisper/Android_App_Whisper"
printf 'sdk.dir=%s\n' "$ANDROID_HOME" > local.properties
export QAIRT_SDK_ROOT="$SD"
bash resolveDependencies.sh
rm -f app/src/main/assets/*fp32* app/src/main/ml/*fp32*
echo "--- populated ---"
ls -la app/src/main/assets app/src/main/ml
ls app/src/main/jniLibs/arm64-v8a
chmod +x gradlew
./gradlew assembleDebug --no-daemon 2>&1 | tail -40
