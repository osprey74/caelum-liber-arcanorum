import { useState } from "react";
import { SPREADS } from "../data/readings";
import type { ReadingSettings, Spread } from "../types/reading";

interface HomeScreenProps {
  settings: ReadingSettings;
  onSettingsChange: (settings: ReadingSettings) => void;
  onStart: (spreadId: Spread["id"], question: string) => void;
  onHistory: () => void;
}

/** Choose a spread, write the question (optional) and start the reading. */
export function HomeScreen({ settings, onSettingsChange, onStart, onHistory }: HomeScreenProps) {
  const [spreadId, setSpreadId] = useState<Spread["id"]>("three");
  const [question, setQuestion] = useState("");
  const spread = SPREADS.find((s) => s.id === spreadId)!;
  const tooMany = settings.scope === "major" && spread.positions.length > 22;

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <header className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="text-3xl tracking-widest text-gold" style={{ fontFamily: '"Shippori Mincho", serif' }}>
            Liber Arcanorum
          </h1>
          <p className="mt-1 text-sm text-ivory/70">スプレッドを選び、心に浮かぶ問いを思い描いてください。</p>
        </div>
        <button type="button" onClick={onHistory} className="rounded border border-gold/40 px-4 py-1.5 text-sm hover:bg-gold/10">
          履歴
        </button>
      </header>

      <section aria-label="スプレッド" className="grid grid-cols-2 gap-4">
        {SPREADS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSpreadId(s.id)}
            className={`rounded-lg border p-4 text-left transition ${
              s.id === spreadId ? "border-gold bg-gold/10" : "border-gold/25 hover:border-gold/60"
            }`}
          >
            <div className="flex items-baseline justify-between">
              <span className="text-lg text-gold">{s.name}</span>
              <span className="text-sm text-ivory/60">{s.positions.length}枚</span>
            </div>
            <p className="mt-1 text-sm text-ivory/75">{s.description}</p>
          </button>
        ))}
      </section>

      <label className="mt-8 block">
        <span className="text-sm text-ivory/80">占いたいこと（任意）</span>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
          maxLength={400}
          placeholder="例：新しい仕事に向けて、今の私に必要なことは？"
          className="mt-2 w-full rounded border border-gold/30 bg-night/60 p-3 text-ivory placeholder:text-ivory/40 focus:border-gold focus:outline-none"
        />
      </label>

      <fieldset className="mt-6 flex flex-wrap gap-x-10 gap-y-3 text-sm">
        <legend className="sr-only">設定</legend>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={settings.useReversed}
            onChange={(e) => onSettingsChange({ ...settings, useReversed: e.target.checked })}
            className="accent-gold"
          />
          逆位置を使う
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={settings.sound !== false}
            onChange={(e) => onSettingsChange({ ...settings, sound: e.target.checked })}
            className="accent-gold"
          />
          効果音
        </label>
        <div className="flex items-center gap-4">
          <span className="text-ivory/80">山札</span>
          {(
            [
              ["all", "78枚すべて"],
              ["major", "大アルカナのみ（22枚）"],
            ] as const
          ).map(([value, label]) => (
            <label key={value} className="flex items-center gap-1.5">
              <input
                type="radio"
                name="scope"
                checked={settings.scope === value}
                onChange={() => onSettingsChange({ ...settings, scope: value })}
                className="accent-gold"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="mt-10 flex justify-center">
        <button
          type="button"
          disabled={tooMany}
          onClick={() => onStart(spreadId, question.trim())}
          className="rounded-full bg-gold px-10 py-3 text-lg text-night shadow-lg transition hover:brightness-110 disabled:opacity-40"
        >
          山札をシャッフルする
        </button>
      </div>
    </div>
  );
}
