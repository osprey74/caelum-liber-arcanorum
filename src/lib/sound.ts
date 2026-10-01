// Sound effects synthesized with the Web Audio API (no audio files, so nothing to license or bundle).

let ctx: AudioContext | null = null;
let noise: AudioBuffer | null = null;
let enabled = true;

export function setSoundEnabled(on: boolean): void {
  enabled = on;
}

function audio(): AudioContext | null {
  if (!enabled) return null;
  try {
    ctx ??= new AudioContext();
    if (ctx.state === "suspended") void ctx.resume();
    return ctx;
  } catch {
    return null; // audio not available: stay silent
  }
}

/** One second of white noise, reused for every effect. */
function noiseBuffer(ac: AudioContext): AudioBuffer {
  if (!noise) {
    noise = ac.createBuffer(1, ac.sampleRate, ac.sampleRate);
    const data = noise.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  }
  return noise;
}

/** A filtered noise burst: the basic "paper" sound of a card. */
function burst(ac: AudioContext, at: number, length: number, freq: number, q: number, gain: number,
               sweepTo?: number): void {
  const src = ac.createBufferSource();
  src.buffer = noiseBuffer(ac);
  const filter = ac.createBiquadFilter();
  filter.type = "bandpass";
  filter.frequency.setValueAtTime(freq, at);
  if (sweepTo) filter.frequency.exponentialRampToValueAtTime(sweepTo, at + length);
  filter.Q.value = q;
  const amp = ac.createGain();
  amp.gain.setValueAtTime(0.0001, at);
  amp.gain.exponentialRampToValueAtTime(gain, at + Math.min(0.012, length / 3));
  amp.gain.exponentialRampToValueAtTime(0.0001, at + length);
  src.connect(filter).connect(amp).connect(ac.destination);
  src.start(at, Math.random() * 0.5, length + 0.05);
}

/** Riffle shuffle: a quick train of card flicks, twice, for about `seconds`. */
export function playShuffle(seconds = 1.3): void {
  const ac = audio();
  if (!ac) return;
  const t0 = ac.currentTime + 0.02;
  const half = seconds / 2;
  for (const start of [0, half]) {
    const flicks = 22;
    for (let i = 0; i < flicks; i++) {
      // flicks speed up towards the end of each riffle
      const t = t0 + start + half * 0.8 * Math.sqrt(i / flicks);
      burst(ac, t, 0.035, 2600 + Math.random() * 1800, 1.4, 0.18 + Math.random() * 0.08);
    }
    // the cards settling into the deck
    burst(ac, t0 + start + half * 0.85, 0.12, 900, 0.8, 0.22);
  }
}

/** Turning one card over: a soft swish with a light tap at the end. */
export function playFlip(): void {
  const ac = audio();
  if (!ac) return;
  const t = ac.currentTime + 0.01;
  burst(ac, t, 0.22, 1500, 0.9, 0.16, 4200);
  burst(ac, t + 0.2, 0.05, 2200, 1.6, 0.12);
}
