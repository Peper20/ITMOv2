// Сквозная проверка ДЗ: повторяющиеся дедлайны (specs/002-recurring-ui + 001-recurring-logic).
// Запуск: node recurring.mjs http://127.0.0.1:8765 [скриншоты-каталог] — сервер на пустой БД.
import puppeteer from "puppeteer-core";

const [base, shots = "."] = process.argv.slice(2);
const json = (path, method = "GET", body) =>
  fetch(base + path, { method, headers: { "Content-Type": "application/json" }, body: body && JSON.stringify(body) }).then((r) => (r.status === 204 ? null : r.json()));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const results = [];
const check = (name, ok, fact) => results.push(`${ok ? "PASS" : "FAIL"}  ${name} — ${fact}`);

const browser = await puppeteer.launch({ executablePath: "/usr/bin/chromium", args: ["--no-sandbox"] });
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });
const notice = () => page.$eval(".live", (el) => el.innerText.trim()).catch(() => "");
const titled = async (t) => (await json("/api/deadlines")).filter((d) => d.title === t);
const open = async (hash) => {
  await page.goto(`${base}/#${hash}`, { waitUntil: "networkidle0" });
  await page.reload({ waitUntil: "networkidle0" }); // хэш читается при старте
};
const card = (day) => `[data-day="${day}"] li.card`;

// 1. Создание с повтором через окно (US1). Шаги 1–3 пишутся в демо-видео hw-demo.webm.
await open("view=week&date=2026-11-06");
const recorder = await page.screencast({ path: `${shots}/hw-demo.webm` });
const pause = () => sleep(900); // чтобы в демо успеть рассмотреть шаг
await page.click("#new-deadline");
await page.waitForSelector("dialog[open] [name=title]");
await page.type("dialog[open] [name=title]", "Отчёт по практике");
await page.$eval("dialog[open] [name=due_at]", (el) => (el.value = ""));
await page.type("dialog[open] [name=due_at]", "06.11.2026");
await page.$eval("dialog[open] [name=due_time]", (el) => (el.value = ""));
await page.type("dialog[open] [name=due_time]", "18:00");
const order = await page.$$eval("dialog[open] [name]", (els) => els.map((e) => e.name));
check("«Повтор» после срока и до приоритета", order.indexOf("recurrence") > order.indexOf("due_time") && order.indexOf("recurrence") < order.indexOf("priority"), order.join(","));
await page.select("dialog[open] [name=recurrence]", "weekly");
await pause();
const hint = await page.$eval("#dd-recurrence-hint", (el) => el.textContent);
check("Подсказка под полем", hint === "Когда отметите выполненным, появится следующий", hint);
await page.click("dialog[open] button[type=submit]");
await page.waitForNetworkIdle();
const [created] = await titled("Отчёт по практике");
check("Создан с recurrence=weekly", created?.recurrence === "weekly", JSON.stringify({ recurrence: created?.recurrence, due: created?.due_at }));
const label = await page.$eval(`${card("2026-11-06")} .open`, (el) => el.getAttribute("aria-label"));
await page.screenshot({ path: `${shots}/hw-badge.png`, clip: { x: 600, y: 60, width: 340, height: 180 } });
await pause();
check("Значок и озвучка повтора", (await page.$(`${card("2026-11-06")} .rep`)) !== null && /повторяется каждую неделю/.test(label), label);

// 2. Отметка → следующий, сообщение, «Показать» (US2)
await page.click(`${card("2026-11-06")} input[type=checkbox]`);
await page.waitForNetworkIdle();
let text = await notice();
check("Сообщение о следующем", text.includes("Следующий — пт, 13 нояб., 18:00"), text);
const focus = await page.evaluate(() => document.activeElement?.type);
check("Фокус остался на флажке", focus === "checkbox", `activeElement.type=${focus}`);
await page.screenshot({ path: `${shots}/hw-notice.png` });
await pause();
check("У выполненного значка нет", (await page.$(`${card("2026-11-06")} .rep`)) === null, "нет .rep");
await page.click(".notice .show");
await page.waitForNetworkIdle();
await pause();
const hash = await page.evaluate(() => location.hash);
const nextCard = await page.$eval(card("2026-11-13"), (el) => el.innerText).catch(() => "");
check("«Показать» → день следующего", hash.includes("date=2026-11-13") && nextCard.includes("Отчёт по практике"), `${hash}; ${nextCard.replace(/\s+/g, " ")}`);

// 3. Снятие отметки и повторная отметка — без дубля (US4, R4)
await open("view=week&date=2026-11-06");
await page.click(`${card("2026-11-06")} input[type=checkbox]`);
await page.waitForNetworkIdle();
text = await notice();
await pause();
check("Снятие: «…остался»", /^Следующий дедлайн( на .*)? остался/.test(text), text);
await page.keyboard.press("Escape");
check("Esc закрывает сообщение", (await notice()) === "", "пусто");
await page.click(`${card("2026-11-06")} input[type=checkbox]`);
await page.waitForNetworkIdle();
text = await notice();
const series = await titled("Отчёт по практике");
await pause();
await recorder.stop();
check("Повторная отметка без сообщения и без дубля", text === "" && series.length === 2, `сообщение «${text}», экземпляров ${series.length}`);

// 4. Двойной клик — один следующий (SC-006)
const dbl = await json("/api/deadlines", "POST", { title: "Двойной", due_at: "2026-11-04T10:00", recurrence: "daily" });
await open("view=week&date=2026-11-04");
const box = await page.$(`${card("2026-11-04")} input[type=checkbox]`);
await box.click();
await box.click();
await page.waitForNetworkIdle();
await sleep(300);
check("Двойной клик → один следующий", (await titled("Двойной")).length === 2, `экземпляров ${(await titled("Двойной")).length}`);
await json(`/api/deadlines/${dbl.id}`, "DELETE");

// 5. Граница: 31-е, «каждый месяц» → 28 февраля (логика, R1/п.2 контракта)
await json("/api/deadlines", "POST", { title: "Аренда", due_at: "2027-01-31T12:00", recurrence: "monthly" });
await open("view=week&date=2027-01-31");
await page.click(`${card("2027-01-31")} input[type=checkbox]`);
await page.waitForNetworkIdle();
text = await notice();
check("31.01 monthly → вс, 28 февр.", text.includes("Следующий — вс, 28 февр., 12:00"), text);

// 6. Автозакрытие через 8 с
await sleep(8500);
check("Сообщение закрылось само через 8 с", (await notice()) === "", "пусто");

// 7. Ошибка сервера по полю «Повтор» показывается под полем (R5)
await page.setRequestInterception(true);
const corrupt = (req) => {
  if (req.method() === "PATCH" && req.url().includes("/api/deadlines/"))
    return req.continue({ postData: JSON.stringify({ ...JSON.parse(req.postData()), recurrence: "hourly" }) });
  req.continue();
};
page.on("request", corrupt);
await page.click(`${card("2027-01-31")} .open`);
await page.waitForSelector("dialog[open] [name=recurrence]");
await page.click("dialog[open] button[type=submit]");
await page.waitForSelector("#dd-recurrence-err");
const err = await page.$eval("#dd-recurrence-err", (el) => el.textContent);
const errFocus = await page.evaluate(() => document.activeElement?.getAttribute("name"));
check("Ошибка recurrence под полем, фокус на поле", err === "Повтор: выберите один из вариантов" && errFocus === "recurrence", `«${err}», фокус ${errFocus}`);
await page.screenshot({ path: `${shots}/hw-field-error.png` });
await page.keyboard.press("Escape");
page.off("request", corrupt);

// 8. Нет связи при отметке: флажок откатывается, полоса ошибки, сообщения нет (US2 сц. 6)
const drop = (req) => (req.method() === "PATCH" ? req.abort("internetdisconnected") : req.continue());
page.on("request", drop);
const before = (await titled("Аренда")).length;
const feb = card("2027-02-28");
await open("view=week&date=2027-02-28");
await page.click(`${feb} input[type=checkbox]`);
await sleep(500);
const checked = await page.$eval(`${feb} input[type=checkbox]`, (el) => el.checked);
const banner = await page.$eval(".banner--error p", (el) => el.textContent).catch(() => "");
page.off("request", drop);
check("Обрыв связи: откат, полоса, без сообщения", !checked && banner.includes("Нет связи") && (await notice()) === "" && (await titled("Аренда")).length === before, `checked=${checked}; «${banner}»`);

await browser.close();
console.log(results.join("\n"));
process.exit(results.some((r) => r.startsWith("FAIL")) ? 1 : 0);
