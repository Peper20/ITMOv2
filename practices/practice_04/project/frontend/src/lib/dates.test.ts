import { describe, expect, it } from "vitest";
import {
  addDays, daysBetween, gridWeeks, inPeriod, inRange, lastDay, mondayOf, parseLocal, parseYmd,
  periodTitle, shiftDate, stamp, visibleRange, ymd,
} from "./dates";

const d = (s: string) => parseYmd(s)!;

describe("разбор и формат", () => {
  it("ymd/stamp дополняют нулями", () => {
    expect(ymd(new Date(2026, 0, 5))).toBe("2026-01-05");
    expect(stamp(new Date(2026, 9, 7, 9, 3))).toBe("2026-10-07T09:03");
  });
  it("parseYmd отвергает несуществующие даты и мусор", () => {
    expect(parseYmd("2026-02-30")).toBeNull();
    expect(parseYmd("2026-13-01")).toBeNull();
    expect(parseYmd("abc")).toBeNull();
    expect(parseYmd(null)).toBeNull();
    expect(ymd(d("2028-02-29"))).toBe("2028-02-29");
  });
  it("parseLocal читает due_at", () => {
    expect(parseLocal("2026-10-10T23:59")).toEqual(new Date(2026, 9, 10, 23, 59));
    expect(parseLocal("")).toBeNull();
  });
});

describe("неделя с понедельника", () => {
  it("mondayOf", () => {
    expect(ymd(mondayOf(d("2026-10-07")))).toBe("2026-10-05"); // ср
    expect(ymd(mondayOf(d("2026-10-11")))).toBe("2026-10-05"); // вс
    expect(ymd(mondayOf(d("2026-10-05")))).toBe("2026-10-05"); // пн
  });
  it("daysBetween через переход на зимнее время", () => {
    expect(daysBetween(d("2026-10-20"), d("2026-11-03"))).toBe(14);
    expect(daysBetween(new Date(2026, 9, 7, 23, 0), new Date(2026, 9, 8, 0, 30))).toBe(1);
  });
});

describe("видимый диапазон", () => {
  it("месяц — полные недели, 5 или 6", () => {
    const oct = visibleRange("month", d("2026-10-15"));
    expect(ymd(oct.first)).toBe("2026-09-28");
    expect(ymd(lastDay(oct))).toBe("2026-11-01");
    expect(oct.days).toBe(35);
    expect(visibleRange("month", d("2026-03-01")).days).toBe(42); // март 2026: с вс до вт
    expect(visibleRange("month", d("2027-02-01")).days).toBe(28); // февраль 2027 ровно 4 недели
  });
  it("неделя — 7 дней с понедельника", () => {
    const w = visibleRange("week", d("2026-10-11"));
    expect(ymd(w.first)).toBe("2026-10-05");
    expect(w.days).toBe(7);
  });
  it("gridWeeks режет по 7", () => {
    const weeks = gridWeeks(visibleRange("month", d("2026-10-01")));
    expect(weeks).toHaveLength(5);
    expect(weeks.every((w) => w.length === 7)).toBe(true);
  });
  it("inRange / inPeriod", () => {
    const r = visibleRange("month", d("2026-10-15"));
    expect(inRange(r, d("2026-09-28"))).toBe(true);
    expect(inRange(r, d("2026-11-02"))).toBe(false);
    expect(inPeriod("month", d("2026-10-15"), d("2026-09-28"))).toBe(false);
    expect(inPeriod("week", d("2026-10-07"), d("2026-10-11"))).toBe(true);
    expect(inPeriod("week", d("2026-10-07"), d("2026-10-12"))).toBe(false);
  });
});

describe("сдвиг периода", () => {
  it("месяц обрезает день до длины месяца", () => {
    expect(ymd(shiftDate("month", d("2026-01-31"), 1))).toBe("2026-02-28");
    expect(ymd(shiftDate("month", d("2026-03-31"), -1))).toBe("2026-02-28");
    expect(ymd(shiftDate("month", d("2026-12-15"), 1))).toBe("2027-01-15");
  });
  it("неделя ±7 дней", () => {
    expect(ymd(shiftDate("week", d("2026-10-07"), -1))).toBe("2026-09-30");
    expect(ymd(addDays(d("2026-10-07"), 7))).toBe("2026-10-14");
  });
});

describe("название периода", () => {
  it("месяц", () => {
    expect(periodTitle("month", visibleRange("month", d("2026-11-30")))).toBe("Ноябрь 2026");
  });
  it("неделя в одном месяце, через месяц, через год", () => {
    expect(periodTitle("week", visibleRange("week", d("2026-10-07")))).toBe("5–11 окт. 2026");
    expect(periodTitle("week", visibleRange("week", d("2026-09-30")))).toBe("28 сент. – 4 окт. 2026");
    expect(periodTitle("week", visibleRange("week", d("2026-12-30")))).toBe("28 дек. 2026 г. – 3 янв. 2027 г.");
  });
});

import { parseTime } from "./dates";

describe("parseTime", () => {
  it("нормализует ввод", () => {
    expect(parseTime("9:05")).toBe("09:05");
    expect(parseTime("0905")).toBe("09:05");
    expect(parseTime("18")).toBe("18:00");
    expect(parseTime(" 23.59 ")).toBe("23:59");
  });
  it("отвергает невозможное", () => {
    expect(parseTime("24:00")).toBeNull();
    expect(parseTime("12:60")).toBeNull();
    expect(parseTime("")).toBeNull();
    expect(parseTime("полдень")).toBeNull();
  });
});

import { formatRuDate, maskRuDate, parseRuDate } from "./dates";

describe("дата ДД.ММ.ГГГГ", () => {
  it("маска подставляет точки и режет лишнее", () => {
    expect(maskRuDate("0")).toBe("0");
    expect(maskRuDate("07")).toBe("07");
    expect(maskRuDate("071")).toBe("07.1");
    expect(maskRuDate("07102026")).toBe("07.10.2026");
    expect(maskRuDate("07.10.20261")).toBe("07.10.2026");
    expect(maskRuDate("7/10-2026")).toBe("71.02.026");
  });
  it("разбор", () => {
    expect(parseRuDate("07.10.2026")).toBe("2026-10-07");
    expect(parseRuDate("7.1.2027")).toBe("2027-01-07");
    expect(parseRuDate("29.02.2028")).toBe("2028-02-29");
    expect(parseRuDate("29.02.2027")).toBeNull();
    expect(parseRuDate("31.04.2026")).toBeNull();
    expect(parseRuDate("07.10.26")).toBeNull();
    expect(parseRuDate("")).toBeNull();
  });
  it("формат туда и обратно", () => {
    expect(formatRuDate("2026-10-07")).toBe("07.10.2026");
    expect(parseRuDate(formatRuDate("2026-01-31"))).toBe("2026-01-31");
  });
});
