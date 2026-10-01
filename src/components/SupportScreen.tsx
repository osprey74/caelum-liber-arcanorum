import { openUrl } from "@tauri-apps/plugin-opener";
import { SUPPORT_EMERGENCY, SUPPORT_LEAD, SUPPORT_LINES } from "../data/support";

interface SupportScreenProps {
  onHome: () => void;
}

/** Shown instead of a reading when the question shows serious distress (handoff §5.3). */
export function SupportScreen({ onHome }: SupportScreenProps) {
  const open = (url: string) => {
    openUrl(url).catch(() => window.open(url, "_blank"));
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center px-6 py-10">
      <div className="rounded-xl border border-teal/50 bg-night/80 p-8 shadow-2xl">
        <div className="space-y-3 leading-relaxed">
          {SUPPORT_LEAD.map((p) => (
            <p key={p}>{p}</p>
          ))}
        </div>
        <ul className="mt-6 space-y-3">
          {SUPPORT_LINES.map((line) => (
            <li key={line.name} className="rounded-lg border border-ivory/15 px-4 py-3">
              <p className="text-ivory">{line.name}</p>
              {line.detail && <p className="text-sm text-ivory/65">{line.detail}</p>}
              {line.contact.startsWith("http") ? (
                <button
                  type="button"
                  onClick={() => open(line.contact)}
                  className="mt-1 break-all text-left text-teal underline underline-offset-2 hover:brightness-125"
                >
                  {line.contact}
                </button>
              ) : (
                <p className="mt-1 text-xl tracking-wider text-gold">{line.contact}</p>
              )}
            </li>
          ))}
        </ul>
        <p className="mt-6 leading-relaxed">{SUPPORT_EMERGENCY}</p>
        <div className="mt-8 flex justify-center">
          <button
            type="button"
            onClick={onHome}
            className="rounded-full border border-gold/60 px-8 py-2.5 text-gold hover:bg-gold/10"
          >
            ホームに戻る
          </button>
        </div>
      </div>
    </div>
  );
}
