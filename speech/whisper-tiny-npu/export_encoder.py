import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
import torch, onnx
import whisper.whisper.model as mm
from whisper.whisper import load_model
print("model.py:", mm.__file__, "| SDPA_AVAILABLE:", mm.SDPA_AVAILABLE)
m = load_model("tiny", device="cpu")
m.eval()
torch.onnx.export(m.encoder, torch.randn(1, 80, 3000), "./whisper_encoder.onnx", opset_version=14)
g = onnx.load("whisper_encoder.onnx")
onnx.checker.check_model(g)
print("inputs:", [(i.name, [d.dim_value for d in i.type.tensor_type.shape.dim]) for i in g.graph.input][:2])
print("EXPORT OK")
