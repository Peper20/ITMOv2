/** Тексты диалога категорий. */
import type { Category, Kind } from "./api";
import { plural } from "./deadlines";

export const KIND_LABEL: Record<Kind, string> = { study: "Учёба", work: "Работа", other: "Другое" };

export function openCountText(c: Category): string {
  const n = c.open_count ?? 0;
  return n ? `${n} ${plural(n, ["открытый дедлайн", "открытых дедлайна", "открытых дедлайнов"])}` : "Открытых дедлайнов нет";
}

export function deleteWarning(c: Category): string {
  const n = c.open_count ?? 0;
  const tail = n ? ` ${n} ${plural(n, ["дедлайн останется", "дедлайна останутся", "дедлайнов останутся"])} без категории.` : "";
  return `Нажмите ещё раз, чтобы удалить «${c.name}».${tail}`;
}
