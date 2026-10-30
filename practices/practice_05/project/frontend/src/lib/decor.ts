/** Классы и цвет категории для полоски/карточки дедлайна. */
import type { Category, Deadline } from "./api";
import { isDone, isOverdue } from "./deadlines";

export function decor(d: Deadline, now: Date, cat: Category | undefined) {
  const cls = ["dl", `p${d.priority}`];
  if (!cat) cls.push("is-nocat");
  if (isOverdue(d, now)) cls.push("is-overdue");
  if (isDone(d)) cls.push("is-done");
  if (d.status === "in_progress") cls.push("is-progress");
  return { class: cls.join(" "), style: cat ? `--cat: ${cat.color}` : undefined };
}
