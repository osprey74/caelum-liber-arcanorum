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
    if (para.length) out.push(<p key={out.length}>{strip(para.join(""))}</p>);
    if (list.length)
      out.push(
        <ul key={out.length} className="list-disc space-y-1 pl-5">
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
      out.push(<h4 key={out.length} className="pt-2 text-gold/90">{strip(line.slice(4))}</h4>);
    } else if (line.startsWith("## ") || line.startsWith("# ")) {
      flush();
      out.push(
        <h3 key={out.length} className="border-b border-gold/25 pb-1 pt-3 text-lg text-gold" style={{ fontFamily: '"Shippori Mincho", serif' }}>
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
  return <div className="space-y-3 leading-relaxed">{out}</div>;
}

/** Drops emphasis markers the model may still write. */
function strip(s: string): string {
  return s.replace(/\*\*(.+?)\*\*/g, "$1").replace(/__(.+?)__/g, "$1");
}
