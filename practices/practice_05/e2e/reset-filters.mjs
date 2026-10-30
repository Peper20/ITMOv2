// Классная работа: сценарии spec deadline-filters в браузере. Аргументы: URL сервера, путь скриншота.
import puppeteer from "puppeteer-core";

const [base, shots = "."] = process.argv.slice(2);
const post = (path, body) =>
  fetch(base + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then((r) => r.json());

const d = new Date();
const day = (n) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(n).padStart(2, "0")}T12:00`;
const cat = await post("/api/categories", { name: "Матан", kind: "study", color: "#3366cc" });
await post("/api/deadlines", { title: "Лаба по матану", due_at: day(10), category_id: cat.id });
await post("/api/deadlines", { title: "Эссе", due_at: day(11) });

const results = [];
const check = (name, ok, fact) => results.push(`${ok ? "PASS" : "FAIL"}  ${name} — ${fact}`);

const browser = await puppeteer.launch({ executablePath: "/usr/bin/chromium", args: ["--no-sandbox"] });
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });
const requests = [];
page.on("request", (r) => r.url().includes("/api/deadlines") && requests.push(r.url()));

await page.goto(base + "/#view=week&date=" + day(10).slice(0, 10), { waitUntil: "networkidle0" });
const chips = () => page.$$eval("[data-day] button, [data-day] .chip", (els) => els.length);
const hasReset = () => page.$('button[aria-label="Сбросить фильтры"]').then(Boolean);
const hash0 = await page.evaluate(() => location.hash);

check("Фильтров нет → кнопки нет", !(await hasReset()), `кнопка: ${await hasReset()}`);
await page.type("#filter-q", "   ");
await new Promise((r) => setTimeout(r, 400));
check("Поиск из пробелов → кнопки нет", !(await hasReset()), `кнопка: ${await hasReset()}`);

// Выбрана категория → кнопка есть
await page.select(".filters__cat select", String(cat.id));
await page.waitForNetworkIdle();
check("Выбрана категория → кнопка есть", await hasReset(), `кнопка: ${await hasReset()}`);
await page.screenshot({ path: `${shots}/reset-active.png`, clip: { x: 0, y: 0, width: 1400, height: 160 } });
const exportFiltered = await page.$eval('a[download="sroki.ics"]', (a) => a.getAttribute("href"));

// Сброс во время набора: вводим и сразу жмём «Сбросить», раньше debounce 300 мс
requests.length = 0;
await page.type("#filter-q", "эссе");
await page.click('button[aria-label="Сбросить фильтры"]');
await new Promise((r) => setTimeout(r, 800));
await page.waitForNetworkIdle();
const st = await page.evaluate(() => ({
  q: document.querySelector("#filter-q").value,
  cat: document.querySelector(".filters__cat select").value,
  focus: document.activeElement?.id,
  hash: location.hash,
  exp: document.querySelector('a[download="sroki.ics"]').getAttribute("href"),
}));
check("Сброс очищает оба фильтра", st.q === "" && st.cat === "", `q="${st.q}", категория="${st.cat}"`);
check("После сброса кнопка скрыта", !(await hasReset()), `кнопка: ${await hasReset()}`);
check("Фокус в поле поиска", st.focus === "filter-q", `activeElement=${st.focus}`);
check("Запрос со старым текстом не ушёл", !requests.some((u) => /[?&]q=[^&]/.test(u)), `запросы: ${requests.map((u) => u.replace(base, "")).join(" | ")}`);
check("Перезагрузка одна (период + боковая)", requests.length === 2, `запросов к /api/deadlines: ${requests.length}`);
check("Экспорт без category_id и q", !/category_id=|[?&]q=/.test(st.exp), `до: ${exportFiltered}; после: ${st.exp}`);
check("Вид/период/хэш не изменились", st.hash === hash0, `хэш до ${hash0}, после ${st.hash}`);
const text = await page.evaluate(() => document.querySelector("main")?.innerText ?? document.body.innerText);
check("Видны все дедлайны периода", text.includes("Лаба по матану") && text.includes("Эссе"), "оба названия на странице");

await page.screenshot({ path: `${shots}/reset.png` });
await browser.close();
console.log(results.join("\n"));
