cd ~/qairt_work/NLPSolution3-AutomaticSpeechRecognition-Whisper/Android_App_Whisper || exit 1
echo "[1/4] copying encoder DLC"
sudo cp ../Generate_Assets/whisper_tiny_encoder_w8a16.dlc app/src/main/assets/
sudo cp ../Generate_Assets/whisper_tiny_encoder_w8a16.dlc app/src/main/ml/
sudo chown vedant:vedant app/src/main/assets/*.dlc app/src/main/ml/*.dlc
echo "[2/4] fixing gradlew line endings"
sed -i 's/\r$//' gradlew
chmod +x gradlew
echo "[3/4] assets and ml now contain:"
ls -la app/src/main/assets app/src/main/ml
echo "[4/4] building (5-10 min, full log in ~/qairt_work/gradle_build.log)"
export ANDROID_HOME=$HOME/android-sdk
./gradlew assembleDebug --no-daemon > ~/qairt_work/gradle_build.log 2>&1
echo "gradle exit code: $?"
tail -40 ~/qairt_work/gradle_build.log
