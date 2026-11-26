/** Состояние приложения на рунах: период, данные, фильтры, открытые окна. */

import { tick } from "svelte";
import { api, type Category, type Deadline, type DeadlineFilters, type Stats } from "./api";
import {
  DAY, addDays, inPeriod, inRange, lastDay, parseLocal, parseYmd, periodTitle, shiftDate, stamp,
  startOfDay, visibleRange, ymd, type View,
} from "./dates";
import { groupByDay } from "./deadlines";
import { formatHash, parseHash } from "./route";

function storageGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}
function storageSet(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* приватный режим — не страшно */
  }
}

/** Фокус на день сетки после перерисовки. */
export async function focusDay(key: string) {
  await tick();
  document.querySelector<HTMLElement>(`[data-day="${key}"]`)?.focus();
}

export type Theme = "system" | "light" | "dark";
const THEMES: Theme[] = ["system", "light", "dark"];

export interface QuickAdd {
  date: string;
  text: string;
  error: string;
  busy: boolean;
}

class AppState {
  view = $state<View>("month");
  anchor = $state(startOfDay(new Date())); // день, задающий период
  cursor = $state(ymd(new Date())); // день с tabindex=0 (roving tabindex)
  flashDate = $state<string | null>(null); // день, к которому перешли из панели
  now = $state(new Date());
  mobile = $state(false);
  sideOpen = $state(true);
  theme = $state<Theme>("system");
  navDir = $state(0); // направление последнего перехода по периодам: -1, 0, 1 (для анимации)
  chipPx = 22; // высота полоски в ячейке месяца (из токенов --chip-h и --chip-h2)
  chip2Px = 38;

  deadlines = $state.raw<Deadline[]>([]);
  loaded = $state(false);
  slow = $state(false); // ответ задерживается — затемняем календарь
  busy = $state(false);
  side = $state.raw<Deadline[]>([]);
  stats = $state.raw<Stats | null>(null);
  categories = $state.raw<Category[]>([]);
  banner = $state("");

  filterCategory = $state(""); // "" — все, "none" — без категории, иначе id
  q = $state("");

  editing = $state<{ deadline: Deadline | null; due: string } | null>(null); // диалог дедлайна
  dayDate = $state<string | null>(null); // окно дня
  categoriesOpen = $state(false);
  qa = $state<QuickAdd | null>(null); // быстрое добавление

  range = $derived(visibleRange(this.view, this.anchor));
  title = $derived(periodTitle(this.view, this.range));
  byDay = $derived(groupByDay(this.deadlines));
  categoryById = $derived(new Map(this.categories.map((c) => [c.id, c])));
  today = $derived(ymd(this.now));
  /** Курсор, гарантированно видимый в сетке. */
  activeDay = $derived(inRange(this.range, parseYmd(this.cursor) ?? this.anchor) ? this.cursor : ymd(this.anchor));
  filters = $derived<DeadlineFilters>({ category_id: this.filterCategory as DeadlineFilters["category_id"], q: this.q.trim() });
  exportHref = $derived(api.exportUrl(this.filters));
  /** Выбранная в фильтре конкретная категория — подставляется в новые дедлайны. */
  presetCategory = $derived(/^\d+$/.test(this.filterCategory) ? Number(this.filterCategory) : null);

  #periodSeq = 0;
  #sideSeq = 0;

  start() {
    const r = parseHash(location.hash, storageGet("sroki.view"), startOfDay(new Date()));
    this.view = r.view;
    this.anchor = r.date;
    this.cursor = ymd(r.date);
    this.sideOpen = storageGet("sroki.side") !== "closed";
    const theme = storageGet("sroki.theme") as Theme | null;
    this.setTheme(theme && THEMES.includes(theme) ? theme : "system");
    const cs = getComputedStyle(document.documentElement);
    this.chipPx = parseFloat(cs.getPropertyValue("--chip-h")) * parseFloat(cs.fontSize) || this.chipPx;
    this.chip2Px = parseFloat(cs.getPropertyValue("--chip-h2")) * parseFloat(cs.fontSize) || this.chip2Px;
    this.#writeHash();
    this.reloadAll();
  }

  #writeHash() {
    history.replaceState(null, "", formatHash({ view: this.view, date: this.anchor }));
    storageSet("sroki.view", this.view);
  }

  /** Тема: системная — без атрибута, иначе <html data-theme>. Без localStorage работает системная. */
  setTheme(theme: Theme) {
    this.theme = theme;
    if (theme === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = theme;
    storageSet("sroki.theme", theme);
  }

  cycleTheme() {
    this.setTheme(THEMES[(THEMES.indexOf(this.theme) + 1) % THEMES.length]);
  }

  toggleSide() {
    this.sideOpen = !this.sideOpen;
    storageSet("sroki.side", this.sideOpen ? "open" : "closed");
  }

  async loadCategories() {
    this.categories = await api.listCategories();
    const id = this.presetCategory;
    if (id !== null && !this.categoryById.has(id)) this.filterCategory = ""; // выбранную удалили
  }

  /** Обновлённая категория — в список без перезагрузки (строки диалога не теряют фокус). */
  applyCategory(c: Category) {
    this.categories = this.categories
      .map((x) => (x.id === c.id ? c : x))
      .sort((a, b) => a.name.localeCompare(b.name, "ru", { sensitivity: "base" }));
  }

  /** Один запрос на видимый период; статус не фильтруем — выполненные тоже видны. */
  async loadPeriod() {
    const seq = ++this.#periodSeq;
    const r = this.range;
    this.busy = true;
    const slow = setTimeout(() => (this.slow = true), 250);
    try {
      const items = await api.listDeadlines({ ...this.filters, from: ymd(r.first), to: ymd(lastDay(r)), sort: "due" });
      if (seq !== this.#periodSeq) return;
      this.deadlines = items;
      this.loaded = true;
      this.banner = "";
    } catch (err) {
      if (seq === this.#periodSeq) this.banner = (err as Error).message;
    } finally {
      clearTimeout(slow);
      if (seq === this.#periodSeq) this.slow = this.busy = false;
    }
  }

  /** Сводка и «Просрочено» / «Ближайшие 7 дней» — без фильтров календаря. */
  async loadSide() {
    const seq = ++this.#sideSeq;
    try {
      const [stats, open] = await Promise.all([
        api.stats(),
        api.listDeadlines({ status: "open", to: stamp(new Date(Date.now() + 7 * DAY)), sort: "due" }),
      ]);
      if (seq !== this.#sideSeq) return;
      this.stats = stats;
      this.side = open;
    } catch {
      /* панель не критична: ошибку связи покажет баннер календаря */
    }
  }

  refresh() {
    this.now = new Date();
    return Promise.all([this.loadPeriod(), this.loadSide()]);
  }

  async reloadAll() {
    try {
      await this.loadCategories();
    } catch (err) {
      this.banner = (err as Error).message;
    }
    await this.refresh();
  }

  /** Перейти к дню (меняет период, если нужно); focus — поставить фокус на этот день. */
  navigateTo(date: Date, { focus = false, reload = false } = {}) {
    const prev = this.anchor;
    const changed = reload || !inRange(this.range, date) || !inPeriod(this.view, this.anchor, date);
    this.anchor = startOfDay(date);
    this.cursor = ymd(date);
    this.#writeHash();
    if (changed) {
      this.navDir = reload ? 0 : Math.sign(date.getTime() - prev.getTime());
      this.deadlines = [];
      this.loaded = false;
      this.loadPeriod();
    }
    if (focus) focusDay(this.cursor);
  }

  /** ‹ › и PageUp/PageDown: тот же день месяца (или недели) в соседнем периоде. */
  shiftPeriod(step: number, focus = false) {
    this.flashDate = null;
    this.navigateTo(shiftDate(this.view, parseYmd(this.cursor) ?? this.anchor, step), { focus });
  }

  goToday(focus = false) {
    this.flashDate = null;
    this.navigateTo(startOfDay(new Date()), { focus });
  }

  setView(view: View) {
    if (view === this.view) return;
    this.view = view;
    this.navigateTo(parseYmd(this.cursor) ?? this.anchor, { reload: true });
  }

  /** Стрелки по сетке: внутри периода — фокус, за краем — листаем. */
  moveCursor(from: string, step: number) {
    const target = addDays(parseYmd(from) ?? this.anchor, step);
    if (inPeriod(this.view, this.anchor, target) && inRange(this.range, target)) focusDay(ymd(target));
    else this.navigateTo(target, { focus: true });
  }

  // --- Окна ---

  /** Срок по умолчанию: завтра 23:59, если сегодня на экране, иначе день-курсор. */
  defaultDue(): string {
    const today = startOfDay(new Date());
    const day = inRange(this.range, today) ? addDays(today, 1) : parseYmd(this.cursor) ?? this.anchor;
    return `${ymd(day)}T23:59`;
  }

  openDeadline(deadline: Deadline | null, due?: string) {
    this.qa = null;
    this.editing = { deadline, due: deadline?.due_at ?? due ?? this.defaultDue() };
  }

  /** Из боковой панели: перейти к дню дедлайна, подсветить его и открыть дедлайн. */
  openFromSide(d: Deadline) {
    this.flashDate = d.due_at.slice(0, 10);
    this.openDeadline(d);
    this.navigateTo(parseLocal(d.due_at) ?? this.anchor);
  }

  openDay(key: string) {
    this.qa = null;
    this.cursor = key;
    this.dayDate = key;
  }

  openQuickAdd(date: string) {
    if (this.qa?.date !== date) this.qa = { date, text: "", error: "", busy: false };
  }

  closeQuickAdd(focus = false) {
    const date = this.qa?.date;
    this.qa = null;
    if (focus && date) focusDay(date);
  }

  async submitQuickAdd() {
    const qa = this.qa;
    if (!qa || qa.busy) return;
    const title = qa.text.trim();
    if (!title) {
      qa.error = "Напишите, что нужно сдать.";
      return;
    }
    qa.busy = true;
    try {
      await api.createDeadline({ title, due_at: `${qa.date}T23:59`, category_id: this.presetCategory });
      this.closeQuickAdd(true);
      await this.refresh();
    } catch (err) {
      qa.busy = false;
      qa.error = (err as Error).message;
    }
  }

  /** Быстрая отметка «готово»; false — не получилось (ошибка в баннере). */
  async setDone(d: Deadline, done: boolean): Promise<boolean> {
    try {
      await api.updateDeadline(d.id, { status: done ? "done" : "todo" });
      await this.refresh();
      return true;
    } catch (err) {
      this.banner = (err as Error).message;
      return false;
    }
  }

  async remove(d: Deadline) {
    try {
      await api.deleteDeadline(d.id);
    } catch (err) {
      if ((err as { status?: number }).status !== 404) {
        this.banner = (err as Error).message;
        return;
      }
    }
    await this.refresh();
  }
}

export const app = new AppState();
