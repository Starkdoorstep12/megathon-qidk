import re, sys, pathlib

p = pathlib.Path(sys.argv[1])
src = p.read_text()
assert "SINGLE_PASS_PATCH" not in src, "already patched"

def body_span(s, name):
    m = re.search(r'class\s+' + name + r'\b[^{]*\{', s)
    assert m, "class %s not found" % name
    i, depth, n = m.end(), 1, len(s)
    while i < n and depth:
        if s.startswith('//', i):
            j = s.find('\n', i); i = n if j < 0 else j; continue
        if s.startswith('/*', i):
            i = s.find('*/', i) + 2; continue
        c = s[i]
        if c in '"\'':
            q = c; i += 1
            while s[i] != q:
                if s[i] == '\\': i += 1
                i += 1
        elif c == '{': depth += 1
        elif c == '}': depth -= 1
        i += 1
    assert depth == 0, "unbalanced braces in %s" % name
    return m.end(), i - 1

REC_BODY = r'''
        @Override
        public void run() {
            final AudioRecord rec = audioRecord;
            byte[] buf = new byte[4096];
            synchronized (fullPcm) { fullPcm.reset(); }
            recordingLatch.countDown();
            while (isRecording && rec != null) {
                int n = rec.read(buf, 0, buf.length);
                if (n > 0) {
                    synchronized (fullPcm) {
                        int room = MAX_PCM_BYTES - fullPcm.size();
                        if (room > 0) fullPcm.write(buf, 0, Math.min(n, room));
                    }
                }
            }
            finishUtterance();   // SINGLE_PASS_PATCH: transcribe once, after Stop
        }
    '''
TR_BODY = r'''
        @Override
        public void run() { /* SINGLE_PASS_PATCH: per-chunk transcription removed */ }
    '''
spans = [body_span(src, "AudioRecordingTask") + (REC_BODY,),
         body_span(src, "TranscriptionTask") + (TR_BODY,)]
spans.sort(key=lambda t: -t[0])
for a, b, new in spans:
    src = src[:a] + new + src[b:]

src, k = re.subn(r'prevMessage\[0\]\s*\+=\s*res\s*;', 'prevMessage[0] += cleanText(res);', src)
assert k == 1, "expected exactly one 'prevMessage[0]+=res;', found %d" % k

HELPERS = r'''
    // ---- SINGLE_PASS_PATCH helpers ----
    private final java.io.ByteArrayOutputStream fullPcm = new java.io.ByteArrayOutputStream();
    private static final int MAX_PCM_BYTES = 16000 * 2 * 30;   // Whisper window = 30 s

    private static String cleanText(String s) {
        if (s == null) return "";
        s = s.replaceAll("\\[[^\\]]*\\]", " ");      // [BLANK_AUDIO], [typing], [Music] ...
        return s.replaceAll("\\s+", " ").trim();
    }

    private static void writeWav(java.io.File f, byte[] pcm) throws java.io.IOException {
        java.nio.ByteBuffer b = java.nio.ByteBuffer.allocate(44).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        b.put("RIFF".getBytes()); b.putInt(36 + pcm.length); b.put("WAVE".getBytes());
        b.put("fmt ".getBytes()); b.putInt(16); b.putShort((short) 1); b.putShort((short) 1);
        b.putInt(16000); b.putInt(32000); b.putShort((short) 2); b.putShort((short) 16);
        b.put("data".getBytes()); b.putInt(pcm.length);
        java.io.FileOutputStream o = new java.io.FileOutputStream(f);
        try { o.write(b.array()); o.write(pcm); } finally { o.close(); }
    }

    private void finishUtterance() {
        byte[] pcm;
        synchronized (fullPcm) { pcm = fullPcm.toByteArray(); }
        if (pcm.length < 16000 * 2 * 3 / 10) {
            Log.d(TAG, "SINGLE_PASS too short: " + pcm.length + " bytes");
            runOnUiThread(new Runnable() { public void run() { audioText.setText("(too short, hold the button while speaking)"); } });
            return;
        }
        double sum = 0; int peak = 0;
        for (int i = 0; i + 1 < pcm.length; i += 2) {
            int v = (short) ((pcm[i] & 0xff) | (pcm[i + 1] << 8));
            sum += (double) v * v; peak = Math.max(peak, Math.abs(v));
        }
        Log.d(TAG, "SINGLE_PASS audio " + (pcm.length / 32) + " ms, rms=" + (int) Math.sqrt(sum / (pcm.length / 2)) + " peak=" + peak);
        runOnUiThread(new Runnable() { public void run() { audioText.setText("Transcribing..."); } });
        long t0 = System.currentTimeMillis();
        try {
            java.io.File f = new java.io.File(getExternalCacheDir(), "utt_" + t0 + ".wav");
            writeWav(f, pcm);
            prevMessage[0] = "";
            java.util.concurrent.CountDownLatch latch = new java.util.concurrent.CountDownLatch(2);
            transcribeAudioChunk(f.getAbsolutePath(), 0, latch);
            boolean ok = latch.await(120, java.util.concurrent.TimeUnit.SECONDS);
            Log.d(TAG, "SINGLE_PASS stop->text " + (System.currentTimeMillis() - t0) + " ms ok=" + ok);
        } catch (Exception e) {
            Log.e(TAG, "SINGLE_PASS failed", e);
        }
    }
'''
j = src.rstrip().rfind('}')
src = src[:j] + HELPERS + "}\n"
p.write_text(src)
print("patched", p)
