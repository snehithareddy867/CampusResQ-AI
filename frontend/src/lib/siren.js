// Web Audio siren tone (no external files). Two-tone alternating oscillator.
let ctx = null;
let playing = false;
let stopTimer = null;

export function playSiren(durationMs = 4000) {
  try {
    if (playing) return;
    playing = true;
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    const now = ctx.currentTime;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.35, now + 0.05);
    gain.connect(ctx.destination);
    const osc = ctx.createOscillator();
    osc.type = "sawtooth";
    // two-tone siren: alternate 700Hz ↔ 1050Hz every 0.35s
    const total = durationMs / 1000;
    let t = now;
    let hi = false;
    while (t < now + total) {
      osc.frequency.setValueAtTime(hi ? 1050 : 700, t);
      t += 0.35;
      hi = !hi;
    }
    osc.connect(gain);
    osc.start(now);
    osc.stop(now + total);
    stopTimer = setTimeout(() => { playing = false; }, durationMs + 50);
  } catch (e) {
    playing = false;
    console.warn("siren failed", e);
  }
}

export function stopSiren() {
  if (stopTimer) { clearTimeout(stopTimer); stopTimer = null; }
  playing = false;
}
