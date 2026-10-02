import { useState } from "react";
import { SPREADS } from "../data/readings";
import { aiAvailable } from "../lib/ai";
import type { ReadingSettings, Spread } from "../types/reading";
import { AboutDialog } from "./AboutDialog";
import { AiSettingsDialog } from "./AiSettingsDialog";
import { Icon } from "./Icon";
import { SpreadSchematic } from "./SpreadSchematic";

interface HomeScreenProps {
  settings: ReadingSettings;
  onSettingsChange: (settings: ReadingSettings) => void;
  onStart: (spreadId: Spread["id"], question: string) => void;
  onHistory: () => void;
}

const pill =
  "flex h-11 items-center gap-2 rounded-full border px-5 text-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-gold";

/** Choose a spread, write the question (optional) and start the reading. */
export function HomeScreen({ settings, onSettingsChange, onStart, onHistory }: HomeScreenProps) {
  const [spreadId, setSpreadId] = useState<Spread["id"]>("three");
  const [question, setQuestion] = useState("");
  const [aiSettings, setAiSettings] = useState(false);
  const [about, setAbout] = useState(false);
  const spread = SPREADS.find((s) => s.id === spreadId)!;
  const tooMany = settings.scope === "major" && spread.positions.length > 22;

  const toggle = (label: string, on: boolean, change: (on: boolean) => void) => (
    <button
      type="button"
      aria-pressed={on}
      onClick={() => change(!on)}
      className={`${pill} px-[18px] ${on ? "border-gold bg-gold/15 text-ivory" : "border-gold/30 text-soft hover:border-gold/60"}`}
    >
      <Icon name={on ? "check" : "dot"} className="h-4 w-4 text-gold" />
      {label}
    </button>
  );

  return (
    <div className="flex min-h-full flex-col">
      <header className="flex items-center justify-between border-b border-gold/20 px-14 py-6">
        <div className="flex items-baseline gap-[18px]">
          <span className="font-display text-2xl font-semibold tracking-[0.26em] text-gold">LIBER ARCANORUM</span>
          <span className="font-display text-sm font-semibold tracking-[0.4em] text-muted">秘儀の書</span>
        </div>
        <nav aria-label="メニュー" className="flex gap-3">
          <button type="button" onClick={onHistory} className={`${pill} border-gold/45 hover:bg-gold/10`}>
            <Icon name="clock" className="h-[18px] w-[18px] text-gold" />
            履歴
          </button>
          {aiAvailable && (
            <button type="button" onClick={() => setAiSettings(true)} className={`${pill} border-gold/45 hover:bg-gold/10`}>
              <Icon name="sparkle" className="h-[18px] w-[18px] text-gold" />
              AIの設定
            </button>
          )}
          <button type="button" onClick={() => setAbout(true)} className={`${pill} border-gold/45 hover:bg-gold/10`}>
            <Icon name="info" className="h-[18px] w-[18px] text-gold" />
            このアプリについて
          </button>
        </nav>
      </header>

      <main className="grid flex-1 gap-16 px-14 pb-10 pt-12 lg:grid-cols-[minmax(360px,460px)_minmax(0,1fr)]">
        <section aria-label="問い" className="flex flex-col gap-7">
          <div className="space-y-3">
            <h1 className="font-display text-[34px] font-semibold leading-[1.45] text-ivory">
              心に浮かぶ問いを、
              <br />
              ひとつ思い描いてください。
            </h1>
            <p className="text-sm leading-[1.8] text-muted">
              問いがなくても占えます。そのときは「いまの自分に必要なこと」を読み解きます。
            </p>
          </div>

          <label className="flex flex-col gap-2.5">
            <span className="text-[13px] tracking-[0.08em] text-soft">占いたいこと（任意）</span>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              maxLength={400}
              placeholder="例：新しい仕事に向けて、今の私に必要なことは？"
              className="h-[132px] w-full resize-none rounded-xl border border-gold/40 bg-deep px-[18px] py-4 text-[15px] leading-[1.7] text-ivory placeholder:text-[#8f8a7c] focus:border-gold focus:outline-none"
            />
          </label>

          <fieldset className="flex flex-col gap-3.5">
            <legend className="mb-3.5 text-[13px] tracking-[0.08em] text-soft">設定</legend>
            <div className="flex flex-wrap gap-2.5">
              {toggle("逆位置を使う", settings.useReversed, (on) => onSettingsChange({ ...settings, useReversed: on }))}
              {toggle("効果音", settings.sound !== false, (on) => onSettingsChange({ ...settings, sound: on }))}
            </div>
            <div role="radiogroup" aria-label="山札" className="flex items-center gap-3.5">
              <span className="text-sm text-soft">山札</span>
              <div className="flex gap-1 rounded-full border border-gold/30 bg-deep p-1">
                {(
                  [
                    ["all", "78枚すべて"],
                    ["major", "大アルカナのみ（22枚）"],
                  ] as const
                ).map(([value, label]) => {
                  const on = settings.scope === value;
                  return (
                    <button
                      key={value}
                      type="button"
                      role="radio"
                      aria-checked={on}
                      onClick={() => onSettingsChange({ ...settings, scope: value })}
                      className={`h-10 rounded-full px-[18px] text-sm transition ${
                        on ? "bg-gold font-medium text-night" : "text-soft hover:text-ivory"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>
          </fieldset>

          <div className="flex-1" />
          <div className="space-y-2">
            <button
              type="button"
              disabled={tooMany}
              onClick={() => onStart(spreadId, question.trim())}
              className="flex h-[60px] w-full items-center justify-center gap-3 rounded-full bg-gold font-display text-[19px] font-semibold tracking-[0.14em] text-night shadow-[0_10px_30px_rgba(0,0,0,0.35)] transition hover:brightness-110 disabled:opacity-40"
            >
              <Icon name="cards" className="h-[22px] w-[22px]" />
              山札をシャッフルする
            </button>
            {tooMany && <p className="text-center text-xs text-muted">大アルカナのみでは、このスプレッドの枚数に足りません。</p>}
          </div>
        </section>

        <section aria-label="スプレッド" className="flex flex-col gap-4">
          <div className="flex items-baseline justify-between">
            <h2 className="font-display text-xl font-semibold tracking-[0.12em] text-gold">スプレッド</h2>
            <span className="text-[13px] text-muted">カードの並べ方を選んでください</span>
          </div>
          <div className="grid flex-1 grid-cols-2 gap-[18px] lg:grid-rows-2">
            {SPREADS.map((s) => {
              const on = s.id === spreadId;
              return (
                <button
                  key={s.id}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setSpreadId(s.id)}
                  className={`relative flex flex-col gap-3.5 rounded-2xl px-6 py-[22px] text-left transition ${
                    on
                      ? "border-[1.5px] border-gold bg-panel-hi shadow-[0_0_0_4px_rgba(201,169,97,0.12)]"
                      : "border border-gold/25 bg-panel hover:border-gold/60"
                  }`}
                >
                  {on && (
                    <span className="absolute right-5 top-5 flex h-7 w-7 items-center justify-center rounded-full bg-gold">
                      <Icon name="check" className="h-4 w-4 text-night" strokeWidth={2.4} />
                    </span>
                  )}
                  <SpreadSchematic spread={s} active={on} />
                  <span className="flex items-baseline gap-3">
                    <span className={`font-display text-xl font-semibold ${on ? "text-gold" : "text-ivory"}`}>{s.name}</span>
                    <span className="text-[13px] text-muted">{s.positions.length}枚</span>
                  </span>
                  <span className="text-sm leading-[1.7] text-soft">{s.description}</span>
                </button>
              );
            })}
          </div>
        </section>
      </main>
      {aiSettings && <AiSettingsDialog onClose={() => setAiSettings(false)} />}
      {about && <AboutDialog onClose={() => setAbout(false)} />}
    </div>
  );
}
