import sys, pathlib
p = pathlib.Path(sys.argv[1]); s = p.read_text()
old = '''    out = subprocess.run(["curl.exe", "-s", URL, "-F", "file=@" + path, "-F", "audio_ctx=%d" % ac,
                          "-F", "temperature=0.0", "-F", "response_format=json"],
                         capture_output=True, text=True, timeout=120).stdout
'''
new = '''    if os.environ.get("FULL_CTX"):
        ac = 0
    cmd = ["curl.exe", "-sS", URL, "-F", "file=@" + path, "-F", "audio_ctx=%d" % ac,
           "-F", "temperature=0.0", "-F", "response_format=json"]
    if os.environ.get("PROMPT"):
        cmd += ["-F", "prompt=" + os.environ["PROMPT"]]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
'''
assert s.count(old) == 1, "anchor not found"
p.write_text(s.replace(old, new)); print("patched")
