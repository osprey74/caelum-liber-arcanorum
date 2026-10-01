import { SAFETY_EMERGENCY, SAFETY_LEAD, SAFETY_LINES } from "../data/support";

/** Police and DV consultation lines, shown before the reading when the question mentions violence or stalking. */
export function SafetyNotice() {
  return (
    <section aria-label="相談窓口のご案内" className="border-b border-teal/40 bg-teal/15 px-6 py-3 text-sm leading-relaxed">
      <p>{SAFETY_LEAD}</p>
      <ul className="mt-1 flex flex-wrap gap-x-6 gap-y-1">
        {SAFETY_LINES.map((line) => (
          <li key={line.name}>
            {line.name}：<span className="tracking-wider text-gold">{line.contact}</span>
            <span className="ml-1 text-xs text-ivory/65">（{line.detail}）</span>
          </li>
        ))}
      </ul>
      <p className="mt-1">{SAFETY_EMERGENCY}</p>
    </section>
  );
}
