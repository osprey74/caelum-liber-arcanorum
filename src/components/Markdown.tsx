import type { ReactNode } from "react";

/**
 * The small Markdown subset the interpretation uses (src/data/interpret-system.md): "## " and "### " headings,
 * "- " list items and paragraphs. Anything else is shown as plain text, never as HTML.
 */
export function Markdown({ text }: { text: string }) {
  const out: ReactNode[] = [];
  let para: string[] = [];
  let list: string[] = [];
  const flush = () => {
    if (para.length)
      out.push(
        <p key={out.length} className="font-mincho text-[15px] leading-[2] text-ivory">
          {strip(para.join(""))}
        </p>,
      );
    if (list.length)
      out.push(
        <ul key={out.length} className="list-disc space-y-1.5 pl-5 font-mincho text-[15px] leading-[1.9] text-ivory marker:text-gold">
          {list.map((li, i) => (
            <li key={i}>{strip(li)}</li>
          ))}
        </ul>,
      );
    para = [];
    list = [];
  };
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) {
      flush();
    } else if (line.startsWith("### ")) {
      flush();
      out.push(
        <h4 key={out.length} className="pt-2 font-display text-[15px] font-semibold text-gold">
          {strip(line.slice(4))}
        </h4>,
      );
    } else if (line.startsWith("## ") || line.startsWith("# ")) {
      flush();
      out.push(
        <h3 key={out.length} className="border-b border-gold/25 pb-2 pt-4 font-display text-lg font-semibold tracking-[0.08em] text-gold first:pt-0">
          {strip(line.replace(/^#+ /, ""))}
        </h3>,
      );
    } else if (/^[-*・] /.test(line)) {
      if (para.length) flush();
      list.push(line.slice(2));
    } else {
      if (list.length) flush();
      para.push(line);
    }
  }
  flush();
  return <div className="space-y-3.5">{out}</div>;
}

/** Drops emphasis markers the model may still write. */
function strip(s: string): string {
  return s.replace(/\*\*(.+?)\*\*/g, "$1").replace(/__(.+?)__/g, "$1");
}
