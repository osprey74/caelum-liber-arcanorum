import { useEffect, useState } from "react";
import { version } from "../../package.json";
import { backImage } from "../data/cards";
import "./SplashScreen.css";

interface SplashScreenProps {
  onDone: () => void;
}

const MIN_MS = 1600; // long enough to read the title, short enough not to wait
const FADE_MS = 450;
/** ?splash keeps the screen up (development screenshots). */
const HOLD = new URLSearchParams(window.location.search).has("splash");

/** Load an image (resolves on error too, so a missing file never blocks the start). */
function preload(src: string): Promise<void> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = img.onerror = () => resolve();
    img.src = src;
  });
}

/** Startup screen: the card back in two gold rings, the title and a progress line, then a fade to home. */
export function SplashScreen({ onDone }: SplashScreenProps) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let cancelled = false;
    const ready = Promise.all([
      preload(backImage("medium")),
      preload(backImage("thumb")),
      document.fonts?.ready ?? Promise.resolve(),
      new Promise((r) => window.setTimeout(r, reduce ? 300 : MIN_MS)),
    ]);
    void ready.then(() => !cancelled && !HOLD && setLeaving(true));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!leaving) return;
    const t = window.setTimeout(onDone, FADE_MS);
    return () => window.clearTimeout(t);
  }, [leaving, onDone]);

  return (
    <div
      className={`splash ${leaving ? "splash--leaving" : ""}`}
      onClick={() => setLeaving(true)}
      role="status"
      aria-label="Liber Arcanorum を起動しています"
    >
      <div className="splash__stage">
        <div className="splash__ring" aria-hidden="true" />
        <div className="splash__ring splash__ring--inner" aria-hidden="true" />
        {(["top", "bottom", "left", "right"] as const).map((side) => (
          <div key={side} className={`splash__tick splash__tick--${side}`} aria-hidden="true" />
        ))}
        <img src={backImage("medium")} alt="" className="splash__card" draggable={false} />
      </div>
      <div className="flex flex-col items-center gap-3.5">
        <h1 className="splash__title font-display">LIBER ARCANORUM</h1>
        <p className="splash__subtitle font-display">秘儀の書</p>
      </div>
      <div className="flex flex-col items-center gap-3">
        <div className="splash__progress" aria-hidden="true">
          <div className="splash__progress-bar" />
        </div>
        <p className="text-[13px] tracking-[0.12em] text-muted">山札を整えています</p>
      </div>
      <div className="absolute inset-x-12 bottom-8 flex justify-between text-xs tracking-[0.16em] text-muted">
        <span>CAELUM SERIES</span>
        <span>v{version}</span>
      </div>
    </div>
  );
}
