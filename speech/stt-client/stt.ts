// On-device STT client: records mic audio in the WebView, sends 16 kHz mono WAV
// to the whisper.cpp server running on the device (localhost:8090).
export const STT_URL = "http://127.0.0.1:8090/inference";
const TARGET_SR = 16000;

/** Whisper audio context (50 frames per second). 0 = full 30 s window. */
export function audioCtxFor(seconds: number): number {
  if (seconds > 20) return 0;
  return Math.min(1500, Math.max(400, Math.ceil(seconds * 50) + 100));
}

export function resampleTo16k(input: Float32Array, srcRate: number): Float32Array {
  if (srcRate === TARGET_SR) return input;
  const ratio = srcRate / TARGET_SR;
  const outLen = Math.floor(input.length / ratio);
  const out = new Float32Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const pos = i * ratio;
    const i0 = Math.floor(pos);
    const i1 = Math.min(i0 + 1, input.length - 1);
    const frac = pos - i0;
    out[i] = input[i0] * (1 - frac) + input[i1] * frac;
  }
  return out;
}

export function encodeWav16(samples: Float32Array, sampleRate = TARGET_SR): Uint8Array {
  const buf = new ArrayBuffer(44 + samples.length * 2);
  const v = new DataView(buf);
  const str = (o: number, s: string) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
  str(0, "RIFF"); v.setUint32(4, 36 + samples.length * 2, true); str(8, "WAVE");
  str(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, sampleRate, true); v.setUint32(28, sampleRate * 2, true);
  v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  str(36, "data"); v.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Uint8Array(buf);
}

export function cleanTranscript(t: string): string {
  return t.replace(/\[[^\]]*\]/g, " ").replace(/\s+/g, " ").trim();
}

export async function transcribe(samples16k: Float32Array, url = STT_URL): Promise<string> {
  const seconds = samples16k.length / TARGET_SR;
  const form = new FormData();
  form.append("file", new Blob([encodeWav16(samples16k).buffer as ArrayBuffer], { type: "audio/wav" }), "utt.wav");
  form.append("audio_ctx", String(audioCtxFor(seconds)));
  form.append("temperature", "0.0");
  form.append("response_format", "json");
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) throw new Error(`STT HTTP ${res.status}`);
  const json = (await res.json()) as { text?: string };
  return cleanTranscript(json.text ?? "");
}

/** Push-to-talk recorder. start() on button down, stop() on release -> 16 kHz samples. */
export class Recorder {
  private ctx?: AudioContext;
  private stream?: MediaStream;
  private node?: ScriptProcessorNode;
  private chunks: Float32Array[] = [];

  async start(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false },
    });
    this.ctx = new AudioContext();
    const src = this.ctx.createMediaStreamSource(this.stream);
    this.node = this.ctx.createScriptProcessor(4096, 1, 1);
    this.chunks = [];
    this.node.onaudioprocess = (e) => this.chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
    src.connect(this.node);
    this.node.connect(this.ctx.destination); // required for onaudioprocess to fire; output is silent
  }

  async stop(): Promise<Float32Array> {
    const rate = this.ctx!.sampleRate;
    this.node!.disconnect();
    this.stream!.getTracks().forEach((t) => t.stop());
    await this.ctx!.close();
    const total = this.chunks.reduce((n, c) => n + c.length, 0);
    const all = new Float32Array(total);
    let o = 0;
    for (const c of this.chunks) { all.set(c, o); o += c.length; }
    this.chunks = [];
    return resampleTo16k(all, rate);
  }
}
