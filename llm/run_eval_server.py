"""Run teammate 2's eval harness against the on-device NPU server.
Usage: python run_eval_server.py --url http://<windows-host>:8081"""
import argparse, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("--extractor-dir", default=os.path.expanduser("~/mega-extractor"))
ap.add_argument("--data", default=None)
ap.add_argument("--url", default=None)
ap.add_argument("--multiturn", action="store_true")
args = ap.parse_args()

sys.path.insert(0, args.extractor_dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval as ev  # teammate 2's eval.py
from server_backend import ServerBackend

data = args.data or os.path.join(args.extractor_dir, "data", "testset.jsonl")
ev.run_eval(data, ServerBackend(args.url), args.multiturn)
