import { useEffect, useRef, useCallback } from "react";

interface VoiceVisualizerProps {
  stream: MediaStream | null;
  isRecording: boolean;
}

// Attempt to reuse a single AudioContext across renders
let sharedCtx: AudioContext | null = null;
function getAudioContext(): AudioContext {
  if (!sharedCtx || sharedCtx.state === "closed") {
    sharedCtx = new AudioContext();
  }
  return sharedCtx;
}

const BAR_COUNT = 48;
const BAR_GAP = 3;
const BAR_MIN_H = 2;
const SMOOTHING = 0.82;
const DECAY = 0.92;

// Amber palette HSL
const BAR_HUE = 35;
const BAR_SAT_BASE = 72;
const BAR_LIT_LO = 48;
const BAR_LIT_HI = 68;

export function VoiceVisualizer({ stream, isRecording }: VoiceVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const smoothedRef = useRef<Float32Array>(new Float32Array(BAR_COUNT));
  const peakRef = useRef<Float32Array>(new Float32Array(BAR_COUNT));
  const elapsedRef = useRef(0);
  const lastTimeRef = useRef(0);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    if (!canvas || !analyser) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const w = rect.width * dpr;
    const h = rect.height * dpr;

    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }

    ctx.clearRect(0, 0, w, h);

    // Time tracking for ambient motion
    const now = performance.now();
    const dt = lastTimeRef.current ? (now - lastTimeRef.current) / 1000 : 0.016;
    lastTimeRef.current = now;
    elapsedRef.current += dt;
    const t = elapsedRef.current;

    // Get frequency data
    const bufLen = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufLen);
    analyser.getByteFrequencyData(dataArray);

    // Map frequency bins to bars (logarithmic distribution — more low-freq resolution)
    const smoothed = smoothedRef.current;
    const peaks = peakRef.current;
    const barW = (w - BAR_GAP * (BAR_COUNT - 1) * dpr) / BAR_COUNT;

    for (let i = 0; i < BAR_COUNT; i++) {
      // Logarithmic bin mapping: more bars for low frequencies
      const ratio = i / BAR_COUNT;
      const logRatio = Math.pow(ratio, 1.6);
      const binStart = Math.floor(logRatio * bufLen * 0.75);
      const binEnd = Math.floor(Math.pow((i + 1) / BAR_COUNT, 1.6) * bufLen * 0.75);
      const count = Math.max(1, binEnd - binStart);

      let sum = 0;
      for (let b = binStart; b < binStart + count && b < bufLen; b++) {
        sum += dataArray[b];
      }
      const raw = sum / count / 255;

      // Smooth with exponential decay
      smoothed[i] = smoothed[i] * SMOOTHING + raw * (1 - SMOOTHING);

      // Peak tracking with slow decay
      if (smoothed[i] > peaks[i]) {
        peaks[i] = smoothed[i];
      } else {
        peaks[i] *= DECAY;
      }
    }

    // Render bars
    const gapPx = BAR_GAP * dpr;
    const minH = BAR_MIN_H * dpr;
    const cornerR = barW * 0.4;

    for (let i = 0; i < BAR_COUNT; i++) {
      const x = i * (barW + gapPx);
      const val = smoothed[i];

      // Ambient idle breathing when quiet
      const breath = Math.sin(t * 1.8 + i * 0.18) * 0.02 + 0.02;
      const displayVal = Math.max(val, breath);

      const barH = Math.max(minH, displayVal * h * 0.88);
      const y = (h - barH) / 2;

      // Color: shift hue slightly per bar, brightness based on amplitude
      const lit = BAR_LIT_LO + (BAR_LIT_HI - BAR_LIT_LO) * displayVal;
      const sat = BAR_SAT_BASE + 10 * displayVal;
      const alpha = 0.45 + 0.55 * displayVal;

      // Bar gradient (bottom to top)
      const grad = ctx.createLinearGradient(x, y + barH, x, y);
      grad.addColorStop(0, `hsla(${BAR_HUE}, ${sat}%, ${lit * 0.7}%, ${alpha * 0.6})`);
      grad.addColorStop(0.5, `hsla(${BAR_HUE}, ${sat}%, ${lit}%, ${alpha})`);
      grad.addColorStop(1, `hsla(${BAR_HUE + 5}, ${sat + 8}%, ${lit + 10}%, ${alpha})`);

      ctx.beginPath();
      roundedRect(ctx, x, y, barW, barH, cornerR);
      ctx.fillStyle = grad;
      ctx.fill();

      // Glow for loud bars
      if (displayVal > 0.25) {
        ctx.save();
        ctx.shadowColor = `hsla(${BAR_HUE}, 80%, 60%, ${displayVal * 0.6})`;
        ctx.shadowBlur = 10 * dpr * displayVal;
        ctx.beginPath();
        roundedRect(ctx, x, y, barW, barH, cornerR);
        ctx.fillStyle = `hsla(${BAR_HUE}, ${sat}%, ${lit}%, ${displayVal * 0.15})`;
        ctx.fill();
        ctx.restore();
      }

      // Peak dot
      if (peaks[i] > 0.08) {
        const peakY = (h - Math.max(minH, peaks[i] * h * 0.88)) / 2 - 3 * dpr;
        const dotAlpha = 0.3 + 0.5 * peaks[i];
        ctx.beginPath();
        ctx.arc(x + barW / 2, peakY, 1.5 * dpr, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${BAR_HUE}, 85%, 72%, ${dotAlpha})`;
        ctx.fill();
      }
    }

    // Center line (subtle)
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.strokeStyle = "rgba(232, 164, 74, 0.06)";
    ctx.lineWidth = 1 * dpr;
    ctx.stroke();

    animRef.current = requestAnimationFrame(draw);
  }, []);

  // Connect stream → analyser
  useEffect(() => {
    if (!stream || !isRecording) {
      // Reset smoothed values when not recording
      smoothedRef.current.fill(0);
      peakRef.current.fill(0);
      return;
    }

    const audioCtx = getAudioContext();
    if (audioCtx.state === "suspended") {
      audioCtx.resume();
    }

    const analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    analyser.smoothingTimeConstant = 0.78;
    analyser.minDecibels = -85;
    analyser.maxDecibels = -10;

    const source = audioCtx.createMediaStreamSource(stream);
    source.connect(analyser);

    analyserRef.current = analyser;
    sourceRef.current = source;
    lastTimeRef.current = 0;

    // Start draw loop
    animRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animRef.current);
      source.disconnect();
      analyserRef.current = null;
      sourceRef.current = null;
    };
  }, [stream, isRecording, draw]);

  // Fade-out draw when recording stops (drain smoothed values)
  useEffect(() => {
    if (isRecording) return;

    let drainFrame = 0;
    const drainLoop = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const smoothed = smoothedRef.current;
      const peaks = peakRef.current;
      let anyActive = false;

      for (let i = 0; i < BAR_COUNT; i++) {
        smoothed[i] *= 0.88;
        peaks[i] *= 0.88;
        if (smoothed[i] > 0.001) anyActive = true;
      }

      if (anyActive) {
        // Reuse draw logic by triggering one more frame
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        const w = rect.width * dpr;
        const h = rect.height * dpr;
        ctx.clearRect(0, 0, w, h);

        const barW = (w - BAR_GAP * (BAR_COUNT - 1) * dpr) / BAR_COUNT;
        const gapPx = BAR_GAP * dpr;
        const minH = BAR_MIN_H * dpr;
        const cornerR = barW * 0.4;

        for (let i = 0; i < BAR_COUNT; i++) {
          const x = i * (barW + gapPx);
          const val = smoothed[i];
          const barH = Math.max(minH, val * h * 0.88);
          const y = (h - barH) / 2;
          const lit = BAR_LIT_LO + (BAR_LIT_HI - BAR_LIT_LO) * val;
          const sat = BAR_SAT_BASE + 10 * val;
          const alpha = 0.45 + 0.55 * val;

          const grad = ctx.createLinearGradient(x, y + barH, x, y);
          grad.addColorStop(0, `hsla(${BAR_HUE}, ${sat}%, ${lit * 0.7}%, ${alpha * 0.6})`);
          grad.addColorStop(0.5, `hsla(${BAR_HUE}, ${sat}%, ${lit}%, ${alpha})`);
          grad.addColorStop(1, `hsla(${BAR_HUE + 5}, ${sat + 8}%, ${lit + 10}%, ${alpha})`);

          ctx.beginPath();
          roundedRect(ctx, x, y, barW, barH, cornerR);
          ctx.fillStyle = grad;
          ctx.fill();
        }

        // Center line
        ctx.beginPath();
        ctx.moveTo(0, h / 2);
        ctx.lineTo(w, h / 2);
        ctx.strokeStyle = "rgba(232, 164, 74, 0.06)";
        ctx.lineWidth = 1 * dpr;
        ctx.stroke();

        drainFrame = requestAnimationFrame(drainLoop);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    };

    drainFrame = requestAnimationFrame(drainLoop);
    return () => cancelAnimationFrame(drainFrame);
  }, [isRecording]);

  return (
    <div className="relative w-full overflow-hidden rounded-lg" style={{ height: 72 }}>
      {/* Background glow layer */}
      <div
        className="absolute inset-0 rounded-lg transition-opacity duration-500"
        style={{
          background: isRecording
            ? "radial-gradient(ellipse 80% 100% at 50% 50%, rgba(232,164,74,0.06) 0%, transparent 70%)"
            : "none",
          opacity: isRecording ? 1 : 0,
        }}
      />
      <canvas
        ref={canvasRef}
        className="block w-full h-full"
        style={{ imageRendering: "auto" }}
      />
      {/* Edge fade masks */}
      <div className="absolute inset-y-0 left-0 w-6 bg-gradient-to-r from-[#1a1917] to-transparent pointer-events-none" />
      <div className="absolute inset-y-0 right-0 w-6 bg-gradient-to-l from-[#1a1917] to-transparent pointer-events-none" />
    </div>
  );
}

/** Draw a rounded rect path (top corners only for bar aesthetic, or all corners). */
function roundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  r = Math.min(r, w / 2, h / 2);
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}
