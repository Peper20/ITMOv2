import { describe, expect, it } from "vitest";
import { ymd } from "./dates";
import { formatHash, parseHash } from "./route";

const today = new Date(2026, 9, 7);

describe("хэш-роутинг", () => {
  it("разбирает вид и дату", () => {
    const r = parseHash("#view=week&date=2026-11-03", null, today);
    expect(r.view).toBe("week");
    expect(ymd(r.date)).toBe("2026-11-03");
  });
  it("по умолчанию — сохранённый вид и сегодня", () => {
    const r = parseHash("", "week", today);
    expect(r.view).toBe("week");
    expect(r.date).toBe(today);
    expect(parseHash("#view=year&date=2026-02-30", null, today)).toEqual({ view: "month", date: today });
  });
  it("туда и обратно", () => {
    const hash = formatHash({ view: "month", date: new Date(2026, 0, 9) });
    expect(hash).toBe("#view=month&date=2026-01-09");
    expect(ymd(parseHash(hash, null, today).date)).toBe("2026-01-09");
  });
});
