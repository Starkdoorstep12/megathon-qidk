import pathlib, sys
ts = pathlib.Path(sys.argv[1] + "/stt-client/stt.ts"); py = pathlib.Path(sys.argv[1] + "/eval/eval_server.py")
a = ts.read_text()
old = '''export function cleanTranscript(t: string): string {
  return t.replace(/\\[[^\\]]*\\]/g, " ").replace(/\\s+/g, " ").trim();
}'''
new = '''export function cleanTranscript(t: string): string {
  const s = t.replace(/\\[[^\\]]*\\]/g, " ").replace(/\\s+/g, " ").trim();
  // Whisper sometimes outputs the whole utterance twice; keep one copy.
  return s.replace(/^(.{15,}?)(?:\\s+\\1)+$/i, "$1");
}'''
assert a.count(old) == 1, "stt.ts anchor not found"
ts.write_text(a.replace(old, new))
b = py.read_text()
old2 = '''    return re.sub(r"\\s+", " ", re.sub(r"\\[[^\\]]*\\]", " ", text)).strip(), time.time() - t0, sec'''
new2 = '''    s = re.sub(r"\\s+", " ", re.sub(r"\\[[^\\]]*\\]", " ", text)).strip()
    s = re.sub(r"^(.{15,}?)(?:\\s+\\1)+$", r"\\1", s, flags=re.I)   # drop whole-utterance repeats
    return s, time.time() - t0, sec'''
assert b.count(old2) == 1, "eval_server.py anchor not found"
py.write_text(b.replace(old2, new2)); print("patched both")
