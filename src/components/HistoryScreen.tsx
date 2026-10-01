import { useState } from "react";
import { CARDS, plateName } from "../data/cards";
import { spreadOf } from "../data/readings";
import { deleteReading, loadHistory } from "../lib/storage";
import type { Reading } from "../types/reading";
import { TarotCard } from "./TarotCard";

interface HistoryScreenProps {
  onOpen: (reading: Reading) => void;
  onBack: () => void;
}

export function HistoryScreen({ onOpen, onBack }: HistoryScreenProps) {
  const [history, setHistory] = useState(loadHistory);

  const remove = (id: string) => {
    if (!window.confirm("この履歴を削除しますか？")) return;
    deleteReading(id);
    setHistory(loadHistory());
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6 flex items-center gap-4">
        <button type="button" onClick={onBack} className="rounded border border-gold/40 px-3 py-1 text-sm hover:bg-gold/10">
          ← 戻る
        </button>
        <h1 className="text-xl text-gold">占いの履歴</h1>
        <span className="text-sm text-ivory/60">{history.length}件</span>
      </header>

      {history.length === 0 && <p className="text-ivory/70">まだ履歴はありません。</p>}

      <ul className="space-y-3">
        {history.map((r) => {
          const spread = spreadOf(r.spreadId);
          return (
            <li key={r.id} className="flex items-center gap-4 rounded-lg border border-gold/20 p-3 hover:border-gold/50">
              <button type="button" onClick={() => onOpen(r)} className="flex min-w-0 flex-1 items-center gap-4 text-left">
                <div className="flex shrink-0 gap-1">
                  {r.cards.slice(0, 5).map((d, i) => (
                    <TarotCard key={i} card={CARDS[d.cardId]} faceUp reversed={d.reversed} size="thumb" width={44} />
                  ))}
                  {r.cards.length > 5 && <span className="self-center pl-1 text-xs text-ivory/60">+{r.cards.length - 5}</span>}
                </div>
                <div className="min-w-0">
                  <p className="text-sm text-gold">
                    {spread.name}
                    <span className="ml-3 text-ivory/60">
                      {new Date(r.createdAt).toLocaleString("ja-JP", { dateStyle: "medium", timeStyle: "short" })}
                    </span>
                  </p>
                  <p className="truncate text-sm text-ivory/85">{r.question || "（問いなし）"}</p>
                  <p className="truncate text-xs text-ivory/55">
                    {r.cards.map((d) => `${plateName(CARDS[d.cardId])}${d.reversed ? "（逆）" : ""}`).join("、")}
                  </p>
                </div>
              </button>
              <button
                type="button"
                onClick={() => remove(r.id)}
                className="shrink-0 rounded border border-gold/30 px-2 py-1 text-xs text-ivory/70 hover:bg-gold/10"
              >
                削除
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
