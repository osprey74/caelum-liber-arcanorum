import { useCallback, useState } from "react";
import { Gallery } from "./components/Gallery";
import { HistoryScreen } from "./components/HistoryScreen";
import { HomeScreen } from "./components/HomeScreen";
import { ReadingScreen } from "./components/ReadingScreen";
import { SplashScreen } from "./components/SplashScreen";
import { SupportScreen } from "./components/SupportScreen";
import { spreadOf } from "./data/readings";
import { needsSupport } from "./lib/crisis";
import { drawCards } from "./lib/deck";
import { setSoundEnabled } from "./lib/sound";
import { loadSettings, saveReading, saveSettings } from "./lib/storage";
import type { Reading, ReadingSettings, Spread } from "./types/reading";

type Screen =
  | { name: "home" }
  | { name: "reading"; reading: Reading; fromHistory: boolean }
  | { name: "history" }
  | { name: "gallery" }
  | { name: "support" };

/**
 * Development entry points: ?gallery opens the card gallery (phase 2); ?history the history;
 * ?demo=<spread id> shows a sample
 * reading with every card face up (not saved), ?detail=<position> also opens that card's detail; ?support the
 * support screen; ?panel opens the demo's interpretation panel.
 */
function startScreen(): Screen {
  const q = new URLSearchParams(window.location.search);
  if (q.has("gallery")) return { name: "gallery" };
  if (q.has("history")) return { name: "history" };
  if (q.has("support")) return { name: "support" };
  const demo = q.get("demo") as Spread["id"] | null;
  if (demo) {
    const spread = spreadOf(demo);
    const reading: Reading = {
      id: "demo",
      createdAt: new Date().toISOString(),
      spreadId: demo,
      question: q.get("q") ?? "これからの一年で大切にしたいことは？",
      settings: { useReversed: true, scope: "all" },
      cards: drawCards(spread.positions.length, "all", true),
    };
    return { name: "reading", reading, fromHistory: true };
  }
  return { name: "home" };
}

const START = startScreen();
const START_DETAIL = Number(new URLSearchParams(window.location.search).get("detail") ?? NaN);

function App() {
  const [screen, setScreen] = useState<Screen>(START);
  const [settings, setSettings] = useState<ReadingSettings>(loadSettings);
  // The startup screen shows on a normal launch only (not on the development entry points).
  const [splash, setSplash] = useState(
    (START.name === "home" && !new URLSearchParams(window.location.search).has("nosplash")) ||
      new URLSearchParams(window.location.search).has("splash"),
  );
  const endSplash = useCallback(() => setSplash(false), []);

  setSoundEnabled(settings.sound !== false);

  const changeSettings = (next: ReadingSettings) => {
    setSettings(next);
    saveSettings(next);
  };

  const start = (spreadId: Spread["id"], question: string) => {
    // A question showing serious distress is not read: the support screen comes first (nothing is saved).
    if (needsSupport(question)) {
      setScreen({ name: "support" });
      return;
    }
    const spread = spreadOf(spreadId);
    const reading: Reading = {
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
      spreadId,
      question,
      settings,
      cards: drawCards(spread.positions.length, settings.scope, settings.useReversed),
    };
    saveReading(reading);
    setScreen({ name: "reading", reading, fromHistory: false });
  };

  if (splash) return <SplashScreen onDone={endSplash} />;

  switch (screen.name) {
    case "gallery":
      return <Gallery />;
    case "support":
      return <SupportScreen onHome={() => setScreen({ name: "home" })} />;
    case "history":
      return (
        <HistoryScreen
          onOpen={(reading) => setScreen({ name: "reading", reading, fromHistory: true })}
          onBack={() => setScreen({ name: "home" })}
        />
      );
    case "reading":
      return (
        <ReadingScreen
          key={screen.reading.id}
          reading={screen.reading}
          fromHistory={screen.fromHistory}
          initialDetail={screen.reading.id === "demo" && START_DETAIL >= 0 ? START_DETAIL : undefined}
          initialPanel={screen.reading.id === "demo" && new URLSearchParams(window.location.search).has("panel")}
          onUpdate={(reading) => reading.id !== "demo" && saveReading(reading)}
          onSupport={() => setScreen({ name: "support" })}
          onBack={() => setScreen(screen.fromHistory ? { name: "history" } : { name: "home" })}
        />
      );
    default:
      return (
        <HomeScreen
          settings={settings}
          onSettingsChange={changeSettings}
          onStart={start}
          onHistory={() => setScreen({ name: "history" })}
        />
      );
  }
}

export default App;
