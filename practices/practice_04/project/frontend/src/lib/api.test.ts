import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, query } from "./api";

afterEach(() => vi.unstubAllGlobals());

function stubFetch(status: number, body: unknown) {
  const fn = vi.fn(async () => new Response(body === undefined ? null : JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

describe("api", () => {
  it("query пропускает пустые значения", () => {
    expect(query({ q: "", category_id: "none", from: "2026-10-01", x: undefined })).toBe("?category_id=none&from=2026-10-01");
    expect(api.exportUrl({})).toBe("/api/export.ics");
  });
  it("GET с фильтрами", async () => {
    const fn = stubFetch(200, []);
    await api.listDeadlines({ from: "2026-10-01", to: "2026-10-31", q: "лаба" });
    expect(fn).toHaveBeenCalledWith("/api/deadlines?from=2026-10-01&to=2026-10-31&q=%D0%BB%D0%B0%D0%B1%D0%B0", expect.anything());
  });
  it("ошибка валидации с полем", async () => {
    stubFetch(400, { error: "Слишком длинно", field: "title" });
    await expect(api.createDeadline({ title: "x", due_at: "2026-10-10T10:00" })).rejects.toMatchObject({ status: 400, field: "title", message: "Слишком длинно" });
  });
  it("409 без поля привязывается к name", async () => {
    stubFetch(409, { error: "Уже есть" });
    await expect(api.createCategory({ name: "A", kind: "study" })).rejects.toMatchObject({ status: 409, field: "name" });
  });
  it("204 — без тела, 500 — общее сообщение, нет связи — status 0", async () => {
    stubFetch(204, undefined);
    await expect(api.deleteDeadline(1)).resolves.toBeUndefined();
    stubFetch(500, { error: "trace" });
    await expect(api.stats()).rejects.toMatchObject({ status: 500, field: null });
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("offline"); }));
    const err = await api.stats().catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(0);
  });
});
