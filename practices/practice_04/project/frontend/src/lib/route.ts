/** Хэш-роутинг: #view=month&date=2026-10-06. Бэкенд не делает SPA-fallback, поэтому только хэш. */

import { parseYmd, ymd, type View } from "./dates";

export interface Route {
  view: View;
  date: Date;
}

/** Разбирает хэш; вид без хэша берётся из сохранённого, дата по умолчанию — сегодня. */
export function parseHash(hash: string, storedView: string | null, today: Date): Route {
  const p = new URLSearchParams(hash.replace(/^#/, ""));
  const view = p.get("view") || storedView;
  return { view: view === "week" ? "week" : "month", date: parseYmd(p.get("date")) ?? today };
}

export const formatHash = (r: Route) => `#view=${r.view}&date=${ymd(r.date)}`;
