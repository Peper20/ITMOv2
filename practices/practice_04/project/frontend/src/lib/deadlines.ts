/** Тексты и группировка дедлайнов — чистые функции, без DOM. */

import type { Deadline, Priority, Status } from "./api";
import { DAY, HOUR, MIN, addDays, daysBetween, fmtDM, fmtLong, fmtWDM, parseLocal, startOfDay, ymd } from "./dates";

export const PRIORITY_LABEL: Record<Priority, string> = { 1: "Низкий", 2: "Обычный", 3: "Высокий" };
export const STATUS_LABEL: Record<Status, string> = { todo: "Не начат", in_progress: "В работе", done: "Выполнен" };

/** Русское множественное число: plural(3, ["день", "дня", "дней"]). */
export function plural(n: number, [one, few, many]: [string, string, string]): string {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

export const countDeadlines = (n: number) => `${n} ${plural(n, ["дедлайн", "дедлайна", "дедлайнов"])}`;

/** Длительность словами: «5 мин», «3 ч», «2 дня». Округляем вниз — для срока честнее. */
export function span(ms: number): string {
  if (ms < HOUR) return `${Math.max(1, Math.floor(ms / MIN))} мин`;
  if (ms < DAY) return `${Math.floor(ms / HOUR)} ч`;
  const n = Math.floor(ms / DAY);
  return `${n} ${plural(n, ["день", "дня", "дней"])}`;
}

export const timeOf = (d: Deadline) => d.due_at.slice(11, 16);
export const dayOf = (d: Deadline) => d.due_at.slice(0, 10);
export const isDone = (d: Deadline) => d.status === "done";
/** Пересчитываем на клиенте, чтобы «просрочено» обновлялось без запроса. */
export const isOverdue = (d: Deadline, now: Date) => !isDone(d) && (parseLocal(d.due_at) ?? now) < now;
export const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/** «сегодня, 18:00» / «завтра, 23:59» / «чт, 8 окт., 23:59» / «просрочено на 2 дня, с 5 окт.». */
export function whenText(d: Deadline, now: Date): string {
  const due = parseLocal(d.due_at) ?? now;
  if (isOverdue(d, now)) return `просрочено на ${span(now.getTime() - due.getTime())}, с ${fmtDM.format(due)}`;
  const diff = daysBetween(now, due);
  return `${diff === 0 ? "сегодня" : diff === 1 ? "завтра" : fmtWDM.format(due)}, ${timeOf(d)}`;
}

/** Описание для чтения с экрана: название, срок, категория, приоритет, статус. */
export function describe(d: Deadline, now: Date, categoryName: string | undefined): string {
  const parts = [d.title, `${fmtLong.format(parseLocal(d.due_at) ?? now)}, ${timeOf(d)}`, categoryName ?? "без категории"];
  if (d.priority !== 2) parts.push(`${PRIORITY_LABEL[d.priority].toLowerCase()} приоритет`);
  if (isOverdue(d, now)) parts.push("просрочен");
  else if (d.status !== "todo") parts.push(STATUS_LABEL[d.status].toLowerCase());
  return parts.join(", ");
}

/** Дедлайны по дням 'YYYY-MM-DD': сначала открытые, потом выполненные; внутри — по времени, затем приоритет. */
export function groupByDay(items: Deadline[]): Map<string, Deadline[]> {
  const map = new Map<string, Deadline[]>();
  for (const d of items) {
    const list = map.get(dayOf(d));
    if (list) list.push(d);
    else map.set(dayOf(d), [d]);
  }
  for (const list of map.values()) {
    list.sort((a, b) => Number(isDone(a)) - Number(isDone(b)) || a.due_at.localeCompare(b.due_at) || b.priority - a.priority);
  }
  return map;
}

/** Открытые дедлайны панели: просроченные и остальные (ближайшие 7 дней). */
export function splitUrgent(items: Deadline[], now: Date): { overdue: Deadline[]; soon: Deadline[] } {
  const overdue: Deadline[] = [];
  const soon: Deadline[] = [];
  for (const d of items) (isOverdue(d, now) ? overdue : soon).push(d);
  return { overdue, soon };
}

/**
 * Сколько полосок показать в ячейке высотой `avail` px (полоска `item` px, зазор `gap`).
 * Если все не влезают — одно место уходит под «ещё N». Всегда показывается хотя бы 0 полосок + «ещё».
 */
export function fitCount(total: number, avail: number, item: number, gap: number): number {
  if (item <= 0) return total;
  const slots = Math.max(1, Math.floor((avail + gap) / (item + gap)));
  return total <= slots ? total : slots - 1;
}

/** Подпись к сроку в диалоге: «через 2 дня» / «через 40 мин» / «просрочено на 3 ч». */
export function relativeDue(due: Date, now: Date): string {
  const ms = due.getTime() - now.getTime();
  return ms >= 0 ? `через ${span(ms)}` : `просрочено на ${span(-ms)}`;
}

export interface DayLoad {
  date: Date;
  count: number;
}

/** Нагрузка на 7 дней с сегодняшнего: число открытых дедлайнов по дням (прошлые дни не считаем). */
export function weekLoad(open: Deadline[], now: Date): DayLoad[] {
  const days = Array.from({ length: 7 }, (_, i) => ({ date: addDays(startOfDay(now), i), count: 0 }));
  const index = new Map(days.map((d, i) => [ymd(d.date), i]));
  for (const d of open) {
    const i = index.get(dayOf(d));
    if (i !== undefined && !isDone(d)) days[i].count++;
  }
  return days;
}

/** Раскладка полосок в ячейке: все влезают высокими (в две строки) — tall; иначе обычные + «ещё N». */
export function chipLayout(total: number, avail: number, item: number, tallItem: number, gap: number) {
  if (total && total * (tallItem + gap) - gap <= avail) return { shown: total, tall: true };
  return { shown: fitCount(total, avail, item, gap), tall: false };
}

/** Время в полоске: 23:59 — значение по умолчанию («к концу дня»), его не показываем. */
export const chipTime = (d: Deadline) => (timeOf(d) === "23:59" ? "" : timeOf(d));
