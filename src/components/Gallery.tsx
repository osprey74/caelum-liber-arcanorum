import { useState } from "react";
import { CARDS } from "../data/cards";
import type { CardSize } from "../types/card";
import { GLYPHS, Glyph } from "./Glyph";
import { TarotCard } from "./TarotCard";

// Development page: every card face up / face down / reversed, with the medallion glyphs and decans.
const PLANET_JA: Record<string, string> = {
  Sun: "太陽", Moon: "月", Mercury: "水星", Venus: "金星", Mars: "火星", Jupiter: "木星", Saturn: "土星",
};
const SIGN_JA: Record<string, string> = {
  Aries: "牡羊座", Taurus: "牡牛座", Gemini: "双子座", Cancer: "蟹座", Leo: "獅子座", Virgo: "乙女座",
  Libra: "天秤座", Scorpio: "蠍座", Sagittarius: "射手座", Capricorn: "山羊座", Aquarius: "水瓶座", Pisces: "魚座",
};
const GROUPS = [
  { key: "all", label: "すべて" },
  { key: "major", label: "大アルカナ" },
  { key: "wands", label: "ワンド" },
  { key: "cups", label: "カップ" },
  { key: "swords", label: "ソード" },
  { key: "pentacles", label: "ペンタクル" },
] as const;
const WIDTHS: Record<CardSize, number> = { thumb: 150, medium: 240, full: 480 };

function Toggle({ on, onClick, children }: { on: boolean; onClick: () => void; children: string }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded border px-3 py-1 text-sm ${on ? "border-gold bg-gold text-night" : "border-gold/40 text-ivory"}`}
    >
      {children}
    </button>
  );
}

type GroupKey = (typeof GROUPS)[number]["key"];

/** Initial settings from the URL, e.g. ?face=0&rev=1&size=medium&group=major&w=256&decan=1 (for screenshots). */
function initial() {
  const q = new URLSearchParams(window.location.search);
  const size = q.get("size");
  const group = q.get("group");
  return {
    faceUp: q.get("face") !== "0",
    reversed: q.get("rev") === "1",
    size: (size === "medium" || size === "full" ? size : "thumb") as CardSize,
    width: Number(q.get("w")) || undefined,
    decan: q.get("decan") === "1",
    group: (GROUPS.some((g) => g.key === group) ? group : "all") as GroupKey,
  };
}

export function Gallery() {
  const [init] = useState(initial);
  const [faceUp, setFaceUp] = useState(init.faceUp);
  const [reversed, setReversed] = useState(init.reversed);
  const [size, setSize] = useState<CardSize>(init.size);
  const [showDecan, setShowDecan] = useState(init.decan);
  const [group, setGroup] = useState<GroupKey>(init.group);
  // Per-card overrides: clicking a card flips it on its own.
  const [flipped, setFlipped] = useState<Set<number>>(new Set());

  const cards = CARDS.filter((c) => group === "all" || (c.suit ?? "major") === group);
  const toggleCard = (id: number) =>
    setFlipped((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return (
    <div className="min-h-screen p-6">
      <header className="mb-6 flex flex-wrap items-center gap-x-6 gap-y-3">
        <h1 className="text-xl tracking-widest text-gold">Liber Arcanorum — カード確認</h1>
        <div className="flex gap-2">
          <Toggle on={faceUp} onClick={() => { setFaceUp(!faceUp); setFlipped(new Set()); }}>
            {faceUp ? "表" : "裏"}
          </Toggle>
          <Toggle on={reversed} onClick={() => setReversed(!reversed)}>逆位置</Toggle>
        </div>
        <div className="flex gap-2">
          {(["thumb", "medium", "full"] as CardSize[]).map((s) => (
            <Toggle key={s} on={size === s} onClick={() => setSize(s)}>{s}</Toggle>
          ))}
        </div>
        <Toggle on={showDecan} onClick={() => setShowDecan(!showDecan)}>デカン表示</Toggle>
        <div className="flex flex-wrap gap-2">
          {GROUPS.map((g) => (
            <Toggle key={g.key} on={group === g.key} onClick={() => setGroup(g.key)}>{g.label}</Toggle>
          ))}
        </div>
      </header>

      <section className="mb-8 flex flex-wrap gap-3" aria-label="記号の一覧">
        {Object.entries(GLYPHS).map(([ch, def]) => (
          <div key={ch} className="flex w-16 flex-col items-center gap-1 text-xs text-ivory/70">
            <Glyph symbol={ch} className="h-9 w-9 text-gold" />
            {def.name}
          </div>
        ))}
      </section>

      <div className="flex flex-wrap gap-5">
        {cards.map((card) => (
          <figure key={card.id} className="flex flex-col items-center gap-1">
            <TarotCard
              card={card}
              faceUp={flipped.has(card.id) ? !faceUp : faceUp}
              reversed={reversed}
              size={size}
              width={init.width ?? WIDTHS[size]}
              onClick={() => toggleCard(card.id)}
            />
            {showDecan && card.decan && (
              <figcaption className="text-xs text-ivory/80">
                {PLANET_JA[card.decan.planet]}・{SIGN_JA[card.decan.sign]} 第{card.decan.decan_no}デカン
              </figcaption>
            )}
          </figure>
        ))}
      </div>
    </div>
  );
}
