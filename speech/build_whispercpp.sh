set -e
cd ~
[ -d whisper.cpp ] || git clone --depth 1 https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
NDK=$(ls -d $HOME/android-sdk/ndk/* | head -1)
echo "NDK: $NDK"
cmake -B build-android -DCMAKE_TOOLCHAIN_FILE=$NDK/build/cmake/android.toolchain.cmake \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-30 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS="-march=armv8.7a" -DCMAKE_CXX_FLAGS="-march=armv8.7a" \
  -DGGML_OPENMP=OFF -DGGML_LLAMAFILE=OFF -DBUILD_SHARED_LIBS=OFF -DWHISPER_BUILD_EXAMPLES=ON
cmake --build build-android -j8 --target whisper-cli whisper-bench
mkdir -p /mnt/c/qidk/wcpp
cp build-android/bin/whisper-cli build-android/bin/whisper-bench /mnt/c/qidk/wcpp/
for m in small.en-q5_1 base.en-q5_1; do
  [ -f /mnt/c/qidk/wcpp/ggml-$m.bin ] || curl -4 -L --fail -o /mnt/c/qidk/wcpp/ggml-$m.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-$m.bin
done
ls -la /mnt/c/qidk/wcpp
