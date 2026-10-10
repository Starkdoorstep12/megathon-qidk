mkdir -p ~/gradle && cd ~/gradle || exit 1
if [ ! -d gradle-8.10.2 ]; then
  echo "[1/2] downloading Gradle 8.10.2"
  curl -fLO https://services.gradle.org/distributions/gradle-8.10.2-bin.zip || exit 1
  unzip -q gradle-8.10.2-bin.zip && rm gradle-8.10.2-bin.zip
fi
cd ~/qairt_work/NLPSolution3-AutomaticSpeechRecognition-Whisper/Android_App_Whisper || exit 1
export ANDROID_HOME=$HOME/android-sdk
echo "[2/2] building (5-10 min, full log in ~/qairt_work/gradle_build.log)"
~/gradle/gradle-8.10.2/bin/gradle assembleDebug --no-daemon > ~/qairt_work/gradle_build.log 2>&1
echo "gradle exit code: $?"
tail -40 ~/qairt_work/gradle_build.log
ls -la app/build/outputs/apk/debug/ 2>/dev/null
