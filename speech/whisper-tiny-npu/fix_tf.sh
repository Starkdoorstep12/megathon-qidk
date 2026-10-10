declare -A M=([opt_einsum]=opt-einsum [pasta]=google-pasta [absl]=absl-py [flatbuffers]=flatbuffers [gast]="gast==0.4.0" [astunparse]=astunparse [termcolor]=termcolor [h5py]=h5py [keras]="keras==2.10.0" [keras_preprocessing]=Keras-Preprocessing [tensorflow_estimator]="tensorflow-estimator==2.10.0" [tensorboard]="tensorboard==2.10.1" [clang]=libclang [grpc]=grpcio)
for i in $(seq 1 20); do
  out=$(python3 -c "import tensorflow as tf; print('TF', tf.__version__)" 2>&1); rc=$?
  if [ $rc -eq 0 ]; then echo "$out" | tail -1; echo "TENSORFLOW OK"; break; fi
  mod=$(echo "$out" | grep -oE "No module named '[^']+'" | head -1 | sed "s/No module named '//; s/'//; s/\..*//")
  if [ -z "$mod" ]; then echo "NON-MISSING-MODULE ERROR:"; echo "$out" | tail -6; break; fi
  pkg=${M[$mod]:-$mod}
  echo "[$i] missing module '$mod' -> installing $pkg"
  pip install -q --no-deps --default-timeout 60 "$pkg" || { echo "pip failed for $pkg"; break; }
done
