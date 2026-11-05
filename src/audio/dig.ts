/**
 * Procedural dig sounds, one per tool. Pure Web Audio synthesis (no samples):
 * every graph is built on any BaseAudioContext, so the same code runs live in
 * an AudioContext and offline in an OfflineAudioContext for testing.
 */
import type { ToolId } from "../art/sprites.ts";

export interface DigVoice {
  /** Fades the voice out from `at` (≈80 ms) and stops every source. */
  stop(at: number): void;
  /** Context time at which the voice ends on its own. */
  readonly end: number;
}

const MASTER_LEVEL = 0.9;

/**
 * Glue compressor + limiter + safety trim between the engine master and the
 * destination. Keeps the loudest moments (excavator clank, ultra boom) at or
 * below about -3 dBFS.
 */
export function createOutputChain(ctx: BaseAudioContext, destination: AudioNode): AudioNode {
  const glue = ctx.createDynamicsCompressor();
  glue.threshold.value = -16;
  glue.knee.value = 10;
  glue.ratio.value = 3;
  glue.attack.value = 0.004;
  glue.release.value = 0.18;
  const limiter = ctx.createDynamicsCompressor();
  limiter.threshold.value = -5;
  limiter.knee.value = 0;
  limiter.ratio.value = 20;
  limiter.attack.value = 0.001;
  limiter.release.value = 0.08;
  const trim = ctx.createGain();
  trim.gain.value = 0.74;
  glue.connect(limiter).connect(trim).connect(destination);
  return glue;
}

const noiseCache = new WeakMap<BaseAudioContext, AudioBuffer>();

/** 2 s of white noise per context, looped with random offsets. */
function whiteNoise(ctx: BaseAudioContext): AudioBuffer {
  const cached = noiseCache.get(ctx);
  if (cached) return cached;
  const frames = Math.floor(ctx.sampleRate * 2);
  const buffer = ctx.createBuffer(1, frames, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < frames; i += 1) data[i] = Math.random() * 2 - 1;
  noiseCache.set(ctx, buffer);
  return buffer;
}

const rand = (min: number, max: number): number => min + Math.random() * (max - min);
const FLOOR = 0.0001;

/** Small toolkit that tracks every source so the voice can be stopped and cleaned up. */
class Rig {
  private readonly sources: AudioScheduledSourceNode[] = [];
  private live = 0;
  private done = false;
  readonly noise: AudioBuffer;
  readonly ctx: BaseAudioContext;
  readonly bus: GainNode;

  constructor(ctx: BaseAudioContext, bus: GainNode) {
    this.ctx = ctx;
    this.bus = bus;
    this.noise = whiteNoise(ctx);
  }

  private track<T extends AudioScheduledSourceNode>(source: T, end: number): T {
    source.stop(end);
    this.sources.push(source);
    this.live += 1;
    source.onended = () => {
      source.disconnect();
      this.live -= 1;
      if (this.live <= 0) this.dispose();
    };
    return source;
  }

  dispose(): void {
    if (this.done) return;
    this.done = true;
    this.bus.disconnect();
  }

  stopAll(at: number): void {
    for (const source of this.sources) {
      try {
        source.stop(at);
      } catch {
        // Already stopped: nothing to do.
      }
    }
  }

  noiseSource(at: number, end: number, rate = 1): AudioBufferSourceNode {
    const source = this.ctx.createBufferSource();
    source.buffer = this.noise;
    source.loop = true;
    source.playbackRate.value = rate;
    source.start(at, Math.random() * 1.8);
    return this.track(source, end);
  }

  osc(
    type: OscillatorType,
    frequency: number,
    at: number,
    end: number,
    detune = 0,
  ): OscillatorNode {
    const osc = this.ctx.createOscillator();
    osc.type = type;
    osc.frequency.setValueAtTime(frequency, at);
    osc.detune.value = detune;
    osc.start(at);
    return this.track(osc, end);
  }

  periodic(wave: PeriodicWave, frequency: number, at: number, end: number): OscillatorNode {
    const osc = this.ctx.createOscillator();
    osc.setPeriodicWave(wave);
    osc.frequency.setValueAtTime(frequency, at);
    osc.start(at);
    return this.track(osc, end);
  }

  filter(type: BiquadFilterType, frequency: number, q = 0.707): BiquadFilterNode {
    const filter = this.ctx.createBiquadFilter();
    filter.type = type;
    filter.frequency.value = frequency;
    filter.Q.value = q;
    return filter;
  }

  gain(value: number): GainNode {
    const gain = this.ctx.createGain();
    gain.gain.value = value;
    return gain;
  }

  /** Percussive envelope: fast attack, exponential decay, connected to the bus. */
  hit(at: number, peak: number, decay: number, attack = 0.002): GainNode {
    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(FLOOR, at);
    gain.gain.exponentialRampToValueAtTime(peak, at + attack);
    gain.gain.exponentialRampToValueAtTime(FLOOR, at + attack + decay);
    gain.connect(this.bus);
    return gain;
  }

  /** Sustained envelope: fade in, hold, fade out, connected to the bus. */
  hold(at: number, end: number, peak: number, fadeIn = 0.04, fadeOut = 0.12): GainNode {
    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0, at);
    gain.gain.linearRampToValueAtTime(peak, at + fadeIn);
    gain.gain.setValueAtTime(peak, Math.max(at + fadeIn, end - fadeOut));
    gain.gain.linearRampToValueAtTime(0, end);
    gain.connect(this.bus);
    return gain;
  }

  /** Low-frequency oscillator added onto `param` with the given depth. */
  lfo(
    param: AudioParam,
    frequency: number,
    depth: number,
    at: number,
    end: number,
    type: OscillatorType = "sine",
  ): OscillatorNode {
    const osc = this.osc(type, frequency, at, end);
    const amount = this.gain(depth);
    osc.connect(amount).connect(param);
    return osc;
  }
}

/* ------------------------------------------------------------------ pá */

function crunch(rig: Rig, at: number, weight: number): void {
  const heavy = weight > 1;
  const body = rig.filter("bandpass", rand(620, 1150) * (heavy ? 0.7 : 1), rand(1, 1.6));
  const soft = rig.filter("lowpass", heavy ? 2600 : 3400, 0.7);
  rig
    .noiseSource(at, at + 0.3 * weight, rand(0.8, 1.2))
    .connect(body)
    .connect(soft)
    .connect(rig.hit(at, 0.7 * weight, rand(0.075, 0.1) * weight));

  rig
    .noiseSource(at, at + 0.08, 1)
    .connect(rig.filter("bandpass", rand(2200, 3000), 1.2))
    .connect(rig.hit(at, 0.3 * weight, 0.035));

  const thump = rig.osc("sine", rand(100, 125) / Math.sqrt(weight), at, at + 0.25 * weight);
  thump.frequency.exponentialRampToValueAtTime(42, at + 0.12 * weight);
  thump.connect(rig.hit(at, 0.55 * weight, 0.11 * weight, 0.003));

  const crackle = rig.gain(0);
  crackle.gain.setValueAtTime(0, at);
  const clicks = Math.round(rand(4, 7) * weight);
  const times = Array.from({ length: clicks }, () => at + rand(0.008, 0.13 * weight)).sort(
    (a, b) => a - b,
  );
  for (const t of times) {
    crackle.gain.setValueAtTime(rand(0.12, 0.3), t);
    crackle.gain.setTargetAtTime(0, t + 0.0005, 0.0012);
  }
  crackle.connect(rig.bus);
  rig
    .noiseSource(at, at + 0.16 * weight, 1)
    .connect(rig.filter("bandpass", rand(2600, 4200), 1.4))
    .connect(crackle);

  if (heavy) {
    rig
      .noiseSource(at + 0.03, at + 0.6, 0.7)
      .connect(rig.filter("lowpass", 700, 0.9))
      .connect(rig.hit(at + 0.03, 0.45, 0.4, 0.01));
  }
}

function pa(rig: Rig, at: number, T: number): number {
  for (let t = 0.02; t < T - 0.5; t += 0.26 * rand(0.9, 1.1)) crunch(rig, at + t, rand(0.85, 1));
  const last = Math.max(0.02, T - 0.34);
  crunch(rig, at + last, 1.6);
  return at + last + 0.65;
}

/* ----------------------------------------------------------- aspirador */

function speedCurve(param: AudioParam, at: number, T: number, base: number, low = 0.35): void {
  const up = Math.min(0.4, T * 0.25);
  const down = Math.min(0.4, T * 0.25);
  param.setValueAtTime(base * low, at);
  param.exponentialRampToValueAtTime(base, at + up);
  param.setValueAtTime(base, at + T - down);
  param.exponentialRampToValueAtTime(base * 0.3, at + T);
}

function aspirador(rig: Rig, at: number, T: number): number {
  const end = at + T;
  const motorBus = rig.hold(at, end, 0.13, 0.08, 0.3);
  const motorTone = rig.filter("lowpass", 1100, 2);
  motorTone.connect(motorBus);
  for (const [type, freq, detune] of [
    ["sawtooth", 148, 0],
    ["sawtooth", 148, 14],
    ["square", 74, -6],
  ] as const) {
    const osc = rig.osc(type, freq, at, end + 0.05, detune);
    speedCurve(osc.frequency, at, T, freq);
    osc.connect(motorTone);
  }
  const whine = rig.osc("sine", 1180, at, end + 0.05);
  speedCurve(whine.frequency, at, T, 1180);
  whine.connect(rig.hold(at, end, 0.03, 0.2, 0.3));

  const airBand = rig.filter("bandpass", 1200, 0.7);
  speedCurve(airBand.frequency, at, T, 3600, 0.33);
  const air = rig.hold(at, end, 0.5, 0.25, 0.35);
  rig.lfo(air.gain, 6.5, 0.07, at, end);
  rig
    .noiseSource(at, end + 0.05)
    .connect(rig.filter("highpass", 900, 0.7))
    .connect(rig.filter("lowpass", 6500, 0.7))
    .connect(airBand)
    .connect(air);

  for (let t = 0.32; t < T - 0.35; t += rand(0.11, 0.3)) {
    const p = at + t;
    rig
      .noiseSource(p, p + 0.06, rand(0.9, 1.2))
      .connect(rig.filter("bandpass", rand(2200, 4500), 3))
      .connect(rig.hit(p, rand(0.35, 0.6), rand(0.018, 0.035), 0.001));
    rig
      .noiseSource(p + 0.004, p + 0.03)
      .connect(rig.filter("bandpass", 4200, 1.5))
      .connect(rig.hit(p + 0.004, 0.25, 0.008, 0.0005));
  }
  return end + 0.06;
}

/* --------------------------------------------------------- escavadeira */

function dieselWave(ctx: BaseAudioContext): PeriodicWave {
  const n = 28;
  const real = new Float32Array(n);
  const imag = new Float32Array(n);
  for (let i = 1; i < n; i += 1) imag[i] = (i % 2 ? 1 : 0.55) / i ** 0.85;
  return ctx.createPeriodicWave(real, imag);
}

function clank(rig: Rig, at: number, weight: number): void {
  const partials = [287, 463, 741, 1183, 1690];
  const shift = rand(0.94, 1.06);
  partials.forEach((f, i) => {
    rig
      .osc("sine", f * shift, at, at + 0.6)
      .connect(rig.hit(at, (0.08 * weight) / Math.sqrt(i + 1), 0.42 / (1 + i * 0.35), 0.001));
  });
  const thump = rig.osc("sine", 78, at, at + 0.5);
  thump.frequency.exponentialRampToValueAtTime(36, at + 0.25);
  thump.connect(rig.hit(at, 0.75 * weight, 0.3, 0.003));
  rig
    .noiseSource(at, at + 0.5, 0.8)
    .connect(rig.filter("lowpass", 850, 0.8))
    .connect(rig.hit(at + 0.005, 0.5 * weight, 0.28, 0.006));
  rig
    .noiseSource(at, at + 0.03)
    .connect(rig.filter("bandpass", 2600, 1.2))
    .connect(rig.hit(at, 0.25 * weight, 0.012, 0.0005));
}

function escavadeira(rig: Rig, at: number, T: number): number {
  const end = at + T;
  const engine = rig.periodic(dieselWave(rig.ctx), 40, at, end + 0.05);
  const chugLfo = rig.osc("square", 20, at, end + 0.05);
  for (let t = 0; t < T; t += 0.07) {
    const phase = t / T;
    const rev = phase < 0.12 ? 38 : phase < 0.6 ? 38 + 14 * ((phase - 0.12) / 0.48) : 47;
    const f = rev * rand(0.96, 1.04);
    engine.frequency.setValueAtTime(f, at + t);
    chugLfo.frequency.setValueAtTime(f / 2, at + t);
  }
  const engineBus = rig.hold(at, end, 0.32, 0.15, 0.3);
  engine.connect(rig.filter("lowpass", 520, 1)).connect(engineBus);

  const chug = rig.gain(0.5);
  const depth = rig.gain(0.5);
  chugLfo.connect(depth).connect(chug.gain);
  rig
    .noiseSource(at, end + 0.05, 0.6)
    .connect(rig.filter("lowpass", 260, 0.8))
    .connect(chug)
    .connect(rig.hold(at, end, 0.55, 0.15, 0.3));

  const sweep = (from: number, to: number, a: number, b: number, level: number): void => {
    const s = at + T * a;
    const e = at + T * b;
    const saw = rig.osc("sawtooth", from, s, e + 0.02);
    saw.frequency.exponentialRampToValueAtTime(to, e - 0.05);
    const band = rig.filter("bandpass", from * 2, 5);
    band.frequency.setValueAtTime(from * 2, s);
    band.frequency.exponentialRampToValueAtTime(to * 2, e - 0.05);
    saw.connect(band).connect(rig.hold(s, e, level, 0.1, 0.12));
    rig.lfo(saw.frequency, 11, 3, s, e);
  };
  sweep(170, 480, 0.1, 0.55, 0.11);
  sweep(240, 400, 0.6, 0.82, 0.08);

  clank(rig, at + T * 0.36, 0.85);
  clank(rig, at + T * 0.66, 0.9);
  const last = Math.max(0.1, T - 0.3);
  clank(rig, at + last, 1.15);
  return at + Math.max(T, last + 0.6) + 0.05;
}

/* --------------------------------------------------------------- broca */

function brocaLayer(
  rig: Rig,
  at: number,
  stop: number,
  T: number,
  level: number,
  fadeOut: number,
): void {
  const up = 0.15;
  const whine = rig.gain(1);
  const tone = rig.filter("lowpass", 2600, 1.2);
  whine.connect(tone).connect(rig.hold(at, stop, 0.085 * level, 0.08, fadeOut));
  for (const [type, mult, amp] of [
    ["sawtooth", 1, 1],
    ["sine", 2, 0.6],
  ] as const) {
    const osc = rig.osc(type, 120 * mult, at, stop + 0.03);
    osc.frequency.exponentialRampToValueAtTime(300 * mult, at + up);
    osc.frequency.exponentialRampToValueAtTime(600 * mult, at + Math.max(up + 0.05, T - 0.25));
    if (stop - at >= T - 0.01) osc.frequency.exponentialRampToValueAtTime(200 * mult, stop);
    rig.lfo(osc.frequency, 9, 4 * mult, at, stop);
    const g = rig.gain(amp);
    osc.connect(g).connect(whine);
  }

  const am = rig.gain(0.55);
  const amLow = rig.gain(0.55);
  const lfo = rig.osc("sine", 30, at, stop + 0.03);
  lfo.frequency.linearRampToValueAtTime(38, stop);
  const depth = rig.gain(0.45);
  lfo.connect(depth);
  depth.connect(am.gain);
  depth.connect(amLow.gain);
  rig
    .noiseSource(at, stop + 0.03)
    .connect(rig.filter("bandpass", 1700, 0.9))
    .connect(am)
    .connect(rig.hold(at, stop, 0.5 * level, 0.1, fadeOut));
  rig
    .noiseSource(at, stop + 0.03, 0.7)
    .connect(rig.filter("lowpass", 450, 0.9))
    .connect(amLow)
    .connect(rig.hold(at, stop, 0.45 * level, 0.1, fadeOut));

  for (let t = 0.12; at + t < stop - 0.12; t += rand(0.08, 0.22)) {
    const p = at + t;
    rig
      .noiseSource(p, p + 0.05)
      .connect(rig.filter("bandpass", rand(2600, 3800), 1.3))
      .connect(rig.hit(p, rand(0.2, 0.38) * level, rand(0.015, 0.03), 0.0005));
    rig
      .osc("triangle", rand(2400, 4600), p, p + 0.06)
      .connect(rig.hit(p, 0.05 * level, 0.03, 0.0005));
  }
}

function broca(rig: Rig, at: number, T: number): number {
  brocaLayer(rig, at, at + T, T, 1, 0.25);
  return at + T + 0.05;
}

/* --------------------------------------------------------- broca-ultra */

function brocaUltra(rig: Rig, at: number, T: number): number {
  const boomAt = at + Math.max(0.3, T - 0.42);
  const pre = boomAt - at;
  brocaLayer(rig, at, boomAt, pre, 0.75, 0.04);

  // FM energy layer: carrier sweeps up, modulation index grows.
  const carrier = rig.osc("sine", 220, at, boomAt + 0.03);
  carrier.frequency.exponentialRampToValueAtTime(880, boomAt);
  const mod = rig.osc("sine", 330, at, boomAt + 0.03);
  mod.frequency.exponentialRampToValueAtTime(1320, boomAt);
  const index = rig.gain(110);
  index.gain.setValueAtTime(110, at);
  index.gain.exponentialRampToValueAtTime(2600, boomAt);
  mod.connect(index).connect(carrier.frequency);
  carrier.connect(rig.hold(at, boomAt, 0.07, 0.25, 0.03));

  // Detuned saw pad through an opening resonant filter.
  const padFilter = rig.filter("lowpass", 400, 5);
  padFilter.frequency.setValueAtTime(400, at);
  padFilter.frequency.exponentialRampToValueAtTime(5200, boomAt);
  padFilter.connect(rig.hold(at, boomAt, 0.07, 0.3, 0.03));
  for (const detune of [-14, 0, 13]) {
    const saw = rig.osc("sawtooth", 110, at, boomAt + 0.03, detune);
    saw.frequency.exponentialRampToValueAtTime(440, boomAt);
    saw.connect(padFilter);
  }

  // Shimmering high partials with independent tremolos.
  [2637, 3520, 4186, 5274].forEach((f, i) => {
    const s = at + pre * 0.3;
    const g = rig.hold(s, boomAt, 0.014, pre * 0.4, 0.03);
    rig.lfo(g.gain, 5 + i * 2.1, 0.01, s, boomAt);
    rig.osc("sine", f, s, boomAt + 0.03).connect(g);
  });

  // Riser.
  const riseBand = rig.filter("bandpass", 500, 2);
  riseBand.frequency.setValueAtTime(500, at);
  riseBand.frequency.exponentialRampToValueAtTime(6500, boomAt);
  const riser = rig.gain(0);
  riser.gain.setValueAtTime(0, at);
  riser.gain.linearRampToValueAtTime(0.28, boomAt - 0.01);
  riser.gain.linearRampToValueAtTime(0, boomAt + 0.01);
  riser.connect(rig.bus);
  rig
    .noiseSource(at, boomAt + 0.03)
    .connect(riseBand)
    .connect(riser);

  // Breakthrough boom.
  const sub = rig.osc("sine", 72, boomAt, boomAt + 1.3);
  sub.frequency.exponentialRampToValueAtTime(27, boomAt + 0.9);
  sub.connect(rig.hit(boomAt, 0.95, 1.1, 0.004));
  const blastFilter = rig.filter("lowpass", 4200, 0.8);
  blastFilter.frequency.setValueAtTime(4200, boomAt);
  blastFilter.frequency.exponentialRampToValueAtTime(90, boomAt + 0.9);
  rig
    .noiseSource(boomAt, boomAt + 1.2, 0.8)
    .connect(blastFilter)
    .connect(rig.hit(boomAt, 0.75, 0.95, 0.003));
  rig
    .noiseSource(boomAt, boomAt + 0.15)
    .connect(rig.filter("bandpass", 2000, 0.8))
    .connect(rig.hit(boomAt, 0.45, 0.08, 0.001));
  for (const f of [523.25, 783.99, 1046.5]) {
    rig
      .osc("sine", f, boomAt + 0.02, boomAt + 1.5)
      .connect(rig.hit(boomAt + 0.02, 0.035, 1.3, 0.01));
  }
  return boomAt + 1.55;
}

/* ------------------------------------------------------------- builder */

const BUILDERS: Record<ToolId, (rig: Rig, at: number, T: number) => number> = {
  pa,
  aspirador,
  escavadeira,
  broca,
  "broca-ultra": brocaUltra,
};

/** Per-tool trim so the five tools land at similar loudness. */
const LEVELS: Record<ToolId, number> = {
  pa: 1.5,
  aspirador: 0.9,
  escavadeira: 1,
  broca: 1,
  "broca-ultra": 1,
};

export function buildDig(
  ctx: BaseAudioContext,
  destination: AudioNode,
  tool: ToolId,
  startAt: number,
  durationSec: number,
): DigVoice {
  const bus = ctx.createGain();
  bus.gain.value = LEVELS[tool];
  bus.connect(destination);
  const rig = new Rig(ctx, bus);
  const T = Math.max(0.6, durationSec);
  const end = BUILDERS[tool](rig, startAt, T);
  let stopped = false;
  return {
    end,
    stop(at: number) {
      if (stopped) return;
      stopped = true;
      bus.gain.cancelScheduledValues(at);
      bus.gain.setValueAtTime(bus.gain.value, at);
      bus.gain.setTargetAtTime(0, at, 0.02);
      rig.stopAll(at + 0.1);
      if (typeof setTimeout === "function" && ctx instanceof AudioContext) {
        setTimeout(() => rig.dispose(), 400);
      }
    },
  };
}

/** Offline render of one dig sound through the same output chain the game uses. */
export async function renderDig(
  tool: ToolId,
  durationMs: number,
  sampleRate = 44100,
): Promise<AudioBuffer> {
  const seconds = durationMs / 1000 + 2;
  const ctx = new OfflineAudioContext(1, Math.ceil(seconds * sampleRate), sampleRate);
  const master = ctx.createGain();
  master.gain.value = MASTER_LEVEL;
  master.connect(createOutputChain(ctx, ctx.destination));
  buildDig(ctx, master, tool, 0.01, durationMs / 1000);
  return ctx.startRendering();
}

export { MASTER_LEVEL };
