import { describe, expect, it } from "vitest";
import type { Deadline } from "./api";
import { countDeadlines, describe as describeDl, fitCount, groupByDay, isOverdue, plural, span, splitUrgent, whenText } from "./deadlines";

const now = new Date(2026, 9, 7, 12, 0);
let seq = 0;
function dl(due_at: string, extra: Partial<Deadline> = {}): Deadline {
  return {
    id: ++seq, title: `Срок ${seq}`, description: "", due_at, category_id: null, priority: 2, status: "todo",
    created_at: "", updated_at: "", completed_at: null, is_overdue: false, ...extra,
  };
}

describe("plural и тексты", () => {
  it("формы числа", () => {
    const f: [string, string, string] = ["день", "дня", "дней"];
    expect([1, 2, 5, 11, 12, 14, 21, 22, 25, 101, 111].map((n) => plural(n, f))).toEqual(
      ["день", "дня", "дней", "дней", "дней", "дней", "день", "дня", "дней", "день", "дней"]);
    expect(countDeadlines(3)).toBe("3 дедлайна");
  });
  it("span округляет вниз", () => {
    expect(span(10_000)).toBe("1 мин");
    expect(span(59 * 60_000)).toBe("59 мин");
    expect(span(5 * 3_600_000 + 1)).toBe("5 ч");
    expect(span(2.9 * 86_400_000)).toBe("2 дня");
  });
});

describe("относительное время", () => {
  it("сегодня, завтра, дальше", () => {
    expect(whenText(dl("2026-10-07T18:00"), now)).toBe("сегодня, 18:00");
    expect(whenText(dl("2026-10-08T23:59"), now)).toBe("завтра, 23:59");
    expect(whenText(dl("2026-10-10T09:00"), now)).toMatch(/^сб, 10 окт\.?, 09:00$/);
  });
  it("просрочено", () => {
    expect(whenText(dl("2026-10-05T10:00"), now)).toBe("просрочено на 2 дня, с 5 окт.");
    expect(whenText(dl("2026-10-07T11:30"), now)).toBe("просрочено на 30 мин, с 7 окт.");
  });
  it("выполненный не просрочен", () => {
    expect(isOverdue(dl("2026-10-01T10:00", { status: "done" }), now)).toBe(false);
    expect(isOverdue(dl("2026-10-01T10:00"), now)).toBe(true);
  });
  it("описание для скринридера", () => {
    const text = describeDl(dl("2026-10-01T10:00", { title: "Лаба", priority: 3 }), now, "ОС");
    expect(text).toBe("Лаба, четверг, 1 октября, 10:00, ОС, высокий приоритет, просрочен");
    expect(describeDl(dl("2026-10-09T10:00", { title: "X", status: "in_progress" }), now, undefined))
      .toBe("X, пятница, 9 октября, 10:00, без категории, в работе");
  });
});

describe("группировка", () => {
  it("по дням: открытые раньше выполненных, затем время и приоритет", () => {
    const a = dl("2026-10-07T18:00", { status: "done" });
    const b = dl("2026-10-07T20:00");
    const c = dl("2026-10-07T09:00", { priority: 1 });
    const e = dl("2026-10-07T09:00", { priority: 3 });
    const f = dl("2026-10-08T09:00");
    const map = groupByDay([a, b, c, e, f]);
    expect(map.get("2026-10-07")!.map((x) => x.id)).toEqual([e.id, c.id, b.id, a.id]);
    expect(map.get("2026-10-08")).toEqual([f]);
  });
  it("панель делится на просроченные и ближайшие", () => {
    const old = dl("2026-10-06T10:00");
    const soon = dl("2026-10-09T10:00");
    expect(splitUrgent([old, soon], now)).toEqual({ overdue: [old], soon: [soon] });
  });
});

describe("fitCount", () => {
  it("все влезают", () => expect(fitCount(3, 100, 22, 2)).toBe(3));
  it("не влезают — место под «ещё N»", () => expect(fitCount(6, 100, 22, 2)).toBe(3));
  it("совсем мало места", () => expect(fitCount(4, 10, 22, 2)).toBe(0));
  it("пустой день", () => expect(fitCount(0, 0, 22, 2)).toBe(0));
});

import { deleteWarning, openCountText } from "./categories";

describe("тексты категорий", () => {
  const c = { id: 1, name: "ОС", kind: "study" as const, color: "#123456", created_at: "", open_count: 2 };
  it("счётчик открытых", () => {
    expect(openCountText(c)).toBe("2 открытых дедлайна");
    expect(openCountText({ ...c, open_count: 0 })).toBe("Открытых дедлайнов нет");
  });
  it("предупреждение об удалении", () => {
    expect(deleteWarning({ ...c, open_count: 1 })).toBe("Нажмите ещё раз, чтобы удалить «ОС». 1 дедлайн останется без категории.");
    expect(deleteWarning({ ...c, open_count: 0 })).toBe("Нажмите ещё раз, чтобы удалить «ОС».");
  });
});

import { relativeDue, weekLoad } from "./deadlines";

describe("подписи и нагрузка", () => {
  it("relativeDue", () => {
    expect(relativeDue(new Date(2026, 9, 9, 13, 0), now)).toBe("через 2 дня");
    expect(relativeDue(new Date(2026, 9, 7, 12, 40), now)).toBe("через 40 мин");
    expect(relativeDue(new Date(2026, 9, 7, 9, 0), now)).toBe("просрочено на 3 ч");
  });
  it("weekLoad считает открытые на 7 дней от сегодня", () => {
    const load = weekLoad([
      dl("2026-10-05T10:00"), // прошлое — не считаем
      dl("2026-10-07T09:00"), // сегодня, уже просрочен — считаем
      dl("2026-10-07T20:00"),
      dl("2026-10-09T10:00", { status: "done" }),
      dl("2026-10-13T23:59"),
      dl("2026-10-14T10:00"), // за горизонтом
    ], now);
    expect(load.map((d) => d.count)).toEqual([2, 0, 0, 0, 0, 0, 1]);
    expect(load[0].date).toEqual(new Date(2026, 9, 7));
  });
});

import { chipLayout, chipTime } from "./deadlines";

describe("раскладка полосок", () => {
  it("высокие, если все влезают в две строки", () => {
    expect(chipLayout(2, 100, 22, 38, 2)).toEqual({ shown: 2, tall: true });
    expect(chipLayout(3, 100, 22, 38, 2)).toEqual({ shown: 3, tall: false });
    expect(chipLayout(6, 100, 22, 38, 2)).toEqual({ shown: 3, tall: false });
    expect(chipLayout(0, 100, 22, 38, 2)).toEqual({ shown: 0, tall: false });
  });
  it("23:59 в полоске не показываем", () => {
    expect(chipTime(dl("2026-10-07T23:59"))).toBe("");
    expect(chipTime(dl("2026-10-07T09:30"))).toBe("09:30");
  });
});
