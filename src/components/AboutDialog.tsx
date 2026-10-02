import { openUrl } from "@tauri-apps/plugin-opener";
import { useEffect } from "react";
import { version } from "../../package.json";
import { backImage } from "../data/cards";
import { Icon } from "./Icon";

export const SITE_URL = "https://arcanorum.osprey74.com";
export const REPO_URL = "https://github.com/osprey74/caelum-liber-arcanorum";

interface AboutDialogProps {
  onClose: () => void;
}

/** Opens a link in the default browser (falls back to a new window outside the desktop app). */
function open(url: string) {
  openUrl(url).catch(() => window.open(url, "_blank", "noopener"));
}

/** "About this app": version, how to use it, links to the site and the source, licenses. */
export function AboutDialog({ onClose }: AboutDialogProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const link = "flex h-11 items-center gap-2 rounded-full border border-gold/45 px-5 text-sm hover:bg-gold/10";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="about-title"
        className="flex max-h-full w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-gold/30 bg-panel shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-6 border-b border-gold/20 px-8 pb-6 pt-7">
          <img src={backImage("thumb")} alt="" className="h-[108px] w-[72px] shrink-0 rounded-md shadow-lg" draggable={false} />
          <div className="min-w-0 flex-1">
            <h2 id="about-title" className="font-display text-2xl font-semibold tracking-[0.24em] text-gold">
              LIBER ARCANORUM
            </h2>
            <p className="mt-1 font-display text-sm font-semibold tracking-[0.4em] text-soft">秘儀の書</p>
            <p className="mt-3 text-sm text-muted">
              バージョン {version} ・ Caelum シリーズのタロット占いアプリ
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-11 w-11 shrink-0 items-center justify-center text-muted hover:text-ivory"
            aria-label="閉じる"
          >
            <Icon name="close" className="h-[18px] w-[18px]" />
          </button>
        </div>

        <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-8 py-6 text-sm leading-[1.8] text-soft">
          <section className="space-y-2">
            <h3 className="font-display text-base font-semibold text-gold">使い方</h3>
            <ol className="list-decimal space-y-1 pl-5">
              <li>ホーム画面で、占いたいこと（任意）を書き、スプレッドを選びます。</li>
              <li>「山札をシャッフルする」を押し、カードを1枚ずつ、またはまとめてめくります。</li>
              <li>カードを選ぶと、そのカードの意味が開きます。すべてめくると、横に解釈が表示されます。</li>
              <li>AI による解釈を使うときは、「AIの設定」で Anthropic の APIキーを登録します（料金はご自身の負担です）。</li>
            </ol>
            <p className="text-muted">占いの結果と解釈は、この PC の中に保存され、「履歴」から読み返せます。</p>
          </section>

          <section className="space-y-2">
            <h3 className="font-display text-base font-semibold text-gold">ご利用にあたって</h3>
            <p>
              タロット占いは、娯楽と内省のための読み物です。結果は未来を断定するものではありません。健康・お金・法律などの大切な判断は、専門家にご相談ください。
            </p>
          </section>

          <section className="space-y-2">
            <h3 className="font-display text-base font-semibold text-gold">ライセンス</h3>
            <ul className="space-y-1">
              <li>プログラム：MIT License</li>
              <li>カードの絵柄（78枚・フレーム・裏面）とアイコン：© 2026 osprey74。無断での転載・再配布・改変はご遠慮ください。</li>
              <li>カード名の書体：Shippori Mincho（SIL Open Font License 1.1、© The Shippori Mincho Project Authors）</li>
            </ul>
          </section>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 border-t border-gold/20 px-8 py-5">
          <button type="button" onClick={() => open(SITE_URL)} className={`${link} bg-gold font-medium text-night hover:bg-gold hover:brightness-110`}>
            公式サイト
          </button>
          <button type="button" onClick={() => open(REPO_URL)} className={link}>
            GitHub
          </button>
          <button type="button" onClick={() => open(`${REPO_URL}/releases`)} className={link}>
            更新情報
          </button>
          <span className="ml-auto text-xs text-muted">© 2026 osprey74</span>
        </div>
      </div>
    </div>
  );
}
