/** Даты в локальном времени: сетка с понедельника, периоды, разбор форматов контракта. */

export type View = "month" | "week";

export const MIN = 60_000;
export const HOUR = 60 * MIN;
export const DAY = 24 * HOUR;

const pad = (n: number) => String(n).padStart(2, "0");

/** Date → 'YYYY-MM-DD'. */
export const ymd = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
/** Date → 'YYYY-MM-DDTHH:MM' (формат due_at). */
export const stamp = (d: Date) => `${ymd(d)}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
/** Полночь дня d + n дней (устойчиво к переходу на летнее время). */
export const addDays = (d: Date, n: number) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
export const startOfDay = (d: Date) => addDays(d, 0);
export const mondayOf = (d: Date) => addDays(d, -((d.getDay() + 6) % 7));
/** Целых суток между полуночами a и b. */
export const daysBetween = (a: Date, b: Date) => Math.round((startOfDay(b).getTime() - startOfDay(a).getTime()) / DAY);
/** Индекс дня недели с понедельника: 0 — пн, 6 — вс. */
export const weekdayIndex = (d: Date) => (d.getDay() + 6) % 7;

/** 'YYYY-MM-DDTHH:MM' → Date или null. */
export function parseLocal(value: string | null | undefined): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(value ?? "");
  return m ? new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) : null;
}

/** 'YYYY-MM-DD' → полночь или null для невалидной даты (2026-02-30 и т. п.). */
export function parseYmd(value: string | null | undefined): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value ?? "");
  if (!m) return null;
  const d = new Date(+m[1], +m[2] - 1, +m[3]);
  return d.getMonth() === +m[2] - 1 && d.getDate() === +m[3] ? d : null;
}

export interface Range {
  first: Date;
  days: number;
}

/** Видимые дни: неделя — 7 дней с понедельника; месяц — полные недели с понедельника. */
export function visibleRange(view: View, anchor: Date): Range {
  if (view === "week") return { first: mondayOf(anchor), days: 7 };
  const first = mondayOf(new Date(anchor.getFullYear(), anchor.getMonth(), 1));
  const last = addDays(mondayOf(new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0)), 6);
  return { first, days: daysBetween(first, last) + 1 };
}

export const lastDay = (r: Range) => addDays(r.first, r.days - 1);
export const inRange = (r: Range, d: Date) => d >= r.first && d < addDays(r.first, r.days);

/** Период в узком смысле: для месяца — сам месяц (соседние дни сетки «за краем»). */
export function inPeriod(view: View, anchor: Date, d: Date): boolean {
  if (view === "week") return inRange(visibleRange(view, anchor), d);
  return d.getMonth() === anchor.getMonth() && d.getFullYear() === anchor.getFullYear();
}

/** Дни сетки по неделям. */
export function gridWeeks(r: Range): Date[][] {
  const weeks: Date[][] = [];
  for (let i = 0; i < r.days; i++) {
    if (i % 7 === 0) weeks.push([]);
    weeks[weeks.length - 1].push(addDays(r.first, i));
  }
  return weeks;
}

/** Соседний период: тот же день месяца (обрезанный до длины месяца) или ±7 дней. */
export function shiftDate(view: View, base: Date, step: number): Date {
  if (view === "week") return addDays(base, 7 * step);
  const len = new Date(base.getFullYear(), base.getMonth() + step + 1, 0).getDate();
  return new Date(base.getFullYear(), base.getMonth() + step, Math.min(base.getDate(), len));
}

const MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
export const WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"];
export const WEEKDAYS_FULL = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"];

export const fmtDM = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short" });
const fmtDMY = new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "short", year: "numeric" });
export const fmtLong = new Intl.DateTimeFormat("ru-RU", { weekday: "long", day: "numeric", month: "long" });
export const fmtWDM = new Intl.DateTimeFormat("ru-RU", { weekday: "short", day: "numeric", month: "short" });

/** Короткое имя месяца для подписи 1-го числа: «нояб.». */
export const monthShort = (d: Date) => fmtDM.format(d).split(/\s/)[1] ?? "";

/** Название периода: «Октябрь 2026» или «5–11 окт. 2026». */
export function periodTitle(view: View, r: Range): string {
  if (view === "month") {
    const mid = addDays(r.first, 7); // вторая неделя сетки всегда в нужном месяце
    return `${MONTHS[mid.getMonth()]} ${mid.getFullYear()}`;
  }
  const first = r.first;
  const last = lastDay(r);
  if (first.getFullYear() !== last.getFullYear()) return `${fmtDMY.format(first)} – ${fmtDMY.format(last)}`;
  const year = ` ${last.getFullYear()}`;
  if (first.getMonth() === last.getMonth()) return `${first.getDate()}–${fmtDM.format(last)}${year}`;
  return `${fmtDM.format(first)} – ${fmtDM.format(last)}${year}`;
}

/** Время от пользователя → 'HH:MM' или null: «9:05», «0905», «18», «23.59». */
export function parseTime(value: string): string | null {
  const m = /^\s*(\d{1,2})(?:[:.\s]?(\d{2}))?\s*$/.exec(value);
  if (!m) return null;
  const h = +m[1];
  const min = m[2] === undefined ? 0 : +m[2];
  return h < 24 && min < 60 ? `${pad(h)}:${pad(min)}` : null;
}

/** Маска ДД.ММ.ГГГГ: оставляет до 8 цифр и подставляет точки по мере ввода. */
export function maskRuDate(value: string): string {
  const d = value.replace(/\D/g, "").slice(0, 8);
  return [d.slice(0, 2), d.slice(2, 4), d.slice(4)].filter(Boolean).join(".");
}

/** 'ДД.ММ.ГГГГ' (день и месяц можно одной цифрой) → 'YYYY-MM-DD' или null для несуществующей даты. */
export function parseRuDate(value: string): string | null {
  const m = /^\s*(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$/.exec(value);
  return m ? (parseYmd(`${m[3]}-${pad(+m[2])}-${pad(+m[1])}`) && `${m[3]}-${pad(+m[2])}-${pad(+m[1])}`) : null;
}

/** 'YYYY-MM-DD' → 'ДД.ММ.ГГГГ'. */
export const formatRuDate = (value: string) => value.slice(0, 10).split("-").reverse().join(".");
