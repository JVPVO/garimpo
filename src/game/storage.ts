import type { Dive } from "./types";

const KEY = "garimpo:v1";

export type Store = {
  dives: Dive[];
  sound: boolean;
  dailyDone: Record<string, { depth: number; tier: number }>;
  streak: { last: string; count: number; freezes: number };
};

const empty: Store = { dives: [], sound: true, dailyDone: {}, streak: { last: "", count: 0, freezes: 0 } };

export function readStore(): Store {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...empty };
    const parsed = JSON.parse(raw) as Partial<Store>;
    return {
      dives: Array.isArray(parsed.dives) ? parsed.dives : [],
      sound: parsed.sound !== false,
      dailyDone: parsed.dailyDone ?? {},
      streak: parsed.streak ?? { last: "", count: 0, freezes: 0 },
    };
  } catch {
    return { ...empty };
  }
}

export function writeStore(store: Store): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(store));
  } catch {
    /* storage full or blocked: the game still works for this session */
  }
}

export function saveDive(dive: Dive): Store {
  const store = readStore();
  store.dives = [dive, ...store.dives.filter((item) => item.id !== dive.id)].slice(0, 120);
  if (dive.mode !== "daily") {
    writeStore(store);
    return store;
  }
  store.dailyDone[dive.date] = { depth: dive.depth, tier: dive.tier };
  const previous = store.streak;
  // A daily dive on the same day already counted; only a new date moves the streak.
  if (previous.last !== dive.date) {
    const yesterday = new Date(`${dive.date}T12:00:00`);
    yesterday.setDate(yesterday.getDate() - 1);
    const y = `${yesterday.getFullYear()}-${String(yesterday.getMonth() + 1).padStart(2, "0")}-${String(yesterday.getDate()).padStart(2, "0")}`;
    if (previous.last === y) {
      store.streak = { ...previous, last: dive.date, count: previous.count + 1 };
    } else if (previous.count > 0 && previous.freezes > 0) {
      store.streak = { last: dive.date, count: previous.count + 1, freezes: previous.freezes - 1 };
    } else {
      store.streak = { last: dive.date, count: 1, freezes: previous.freezes };
    }
    if ((store.streak.count + 1) % 4 === 0) store.streak.freezes += 1;
  }
  writeStore(store);
  return store;
}

export function bestDepth(store: Store): number {
  return store.dives.reduce((best, dive) => Math.max(best, dive.depth), 0);
}
