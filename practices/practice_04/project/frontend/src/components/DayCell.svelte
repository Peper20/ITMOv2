<script lang="ts">
  import { app } from "../lib/app.svelte";
  import { WEEKDAYS, fmtLong, monthShort, weekdayIndex, ymd } from "../lib/dates";
  import { chipLayout, countDeadlines } from "../lib/deadlines";
  import Chip from "./Chip.svelte";
  import DeadlineCard from "./DeadlineCard.svelte";
  import QuickAdd from "./QuickAdd.svelte";

  let { date, week, other }: { date: Date; week: boolean; other: boolean } = $props();

  const GAP = 2; // зазор между полосками (.list gap)
  const key = $derived(ymd(date));
  const list = $derived(app.byDay.get(key) ?? []);
  const today = $derived(key === app.today);
  const tab = $derived(key === app.activeDay ? 0 : -1);
  const dotMode = $derived(!week && app.mobile); // телефон: месяц — точки, тап открывает окно дня
  let avail = $state(0);
  const layout = $derived(week || dotMode ? { shown: list.length, tall: false } : chipLayout(list.length, avail, app.chipPx, app.chip2Px, GAP));
  const shown = $derived(layout.shown);
  const weekend = $derived(weekdayIndex(date) >= 5);
  const skeleton = $derived(app.slow && !app.loaded ? (date.getDate() * 7) % 3 : 0); // 0–2 заглушки, стабильно по дате
  const label = $derived(`${fmtLong.format(date)}${today ? ", сегодня" : ""}: ${list.length ? countDeadlines(list.length) : "дедлайнов нет"}`);

  function onclick(e: MouseEvent) {
    const t = e.target as HTMLElement;
    if (t.closest(".qa")) return;
    if (dotMode || t.closest(".num, .more")) return app.openDay(key);
    if (t.closest("button, input, label, .card")) return;
    app.openQuickAdd(key);
  }

  function onkeydown(e: KeyboardEvent) {
    if (e.target !== e.currentTarget || e.altKey || e.ctrlKey || e.metaKey) return;
    const step = ({ ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 } as Record<string, number>)[e.key];
    if (step) {
      e.preventDefault();
      app.moveCursor(key, step);
    } else if (e.key === "Enter") {
      e.preventDefault();
      app.openQuickAdd(key);
    }
  }
</script>

<div
  class="day"
  class:is-week={week}
  class:is-other={other}
  class:is-today={today}
  class:is-weekend={weekend}
  class:is-flash={key === app.flashDate}
  role="gridcell"
  tabindex={tab}
  data-day={key}
  aria-label={label}
  aria-current={today ? "date" : undefined}
  {onclick}
  {onkeydown}
  onfocusin={() => (app.cursor = key)}
>
  <div class="head">
    <button type="button" class="num" tabindex={tab} aria-label="Все сроки дня: {fmtLong.format(date)}">
      <span class="num__d display">{date.getDate()}</span>
      {#if week}<span class="num__wd">{WEEKDAYS[weekdayIndex(date)]}</span>{/if}
      {#if !week && date.getDate() === 1}<span class="num__wd">{monthShort(date)}</span>{/if}
    </button>
    {#if week && today}<span class="today-label">сегодня</span>{/if}
    <span class="add" aria-hidden="true">+</span>
  </div>

  {#if skeleton}
    <div class="list" aria-hidden="true">
      {#each Array(skeleton) as _, i (i)}<span class="skeleton" style="width: {90 - i * 25}%"></span>{/each}
    </div>
  {:else if week}
    <ol class="list">
      {#each list as d (d.id)}<DeadlineCard {d} {tab} />{:else}<li class="free">Сроков нет</li>{/each}
    </ol>
  {:else}
    <ul class="list" bind:clientHeight={avail}>
      {#each list.slice(0, shown) as d (d.id)}<li><Chip {d} tab={dotMode ? -1 : tab} tall={layout.tall} /></li>{/each}
      {#if shown < list.length}
        <li>
          <button type="button" class="more" tabindex={tab} aria-label="Ещё {countDeadlines(list.length - shown)}, все сроки дня">
            ещё {list.length - shown}
          </button>
        </li>
      {/if}
    </ul>
  {/if}

  {#if app.qa?.date === key}<QuickAdd />{/if}
</div>

<style>
  .day {
    position: relative;
    display: flex; flex-direction: column; min-height: 0; min-width: 0;
    padding-bottom: var(--sp-1);
    background: var(--tile);
    box-shadow: var(--shadow-tile);
    cursor: cell;
    transition: background-color var(--t);
  }
  .day.is-weekend { background: var(--tile-weekend); }
  .day.is-other { background: var(--tile-off); box-shadow: none; }
  .day:focus-visible { outline-offset: -2px; }
  .day.is-flash { box-shadow: inset 0 0 0 2px var(--focus); animation: flash 1.2s var(--ease); }
  @keyframes flash { 0%, 30% { background: color-mix(in oklab, var(--focus) 14%, var(--tile)); } }
  .day.is-today { box-shadow: inset 0 3px 0 var(--signal), var(--shadow-tile); }

  .head { display: flex; align-items: center; gap: var(--sp-1); min-height: 1.75rem; padding: 3px var(--sp-1) 1px; }
  .num {
    display: inline-flex; align-items: baseline; gap: 0.3rem;
    min-width: 1.6rem; height: 1.5rem; padding: 0 0.3rem;
    border: 0; border-radius: var(--r-s); background: transparent; color: var(--ink);
    cursor: pointer; transition: background-color var(--t);
  }
  .num:hover { background: var(--wash-2); }
  .num__d { font-size: var(--fs-lg); line-height: 1.35; }
  .num__wd { font-size: var(--fs-xs); font-weight: 500; color: var(--ink-3); }
  .is-weekend .num__d { color: var(--weekend-ink); }
  .is-other .num__d { color: var(--ink-3); }
  .is-other .num { opacity: 0.85; }
  /* «Сегодня» — жёлтый магнит на числе */
  .is-today .num { background: var(--signal); box-shadow: 0 1px 0 rgb(0 0 0 / 0.18), 0 2px 6px -2px color-mix(in oklab, var(--signal) 70%, transparent); }
  .is-today .num :is(.num__d, .num__wd) { color: var(--on-signal); }
  .is-today .num:hover { background: color-mix(in oklab, var(--signal) 85%, white); }
  .today-label { font-size: var(--fs-xs); font-weight: 600; color: var(--ink-2); }

  .add {
    margin-left: auto; width: 1.25rem; height: 1.25rem; display: grid; place-items: center;
    border-radius: var(--r-xs); color: var(--ink-3); font-size: var(--fs-md); line-height: 1;
    opacity: 0; transition: opacity var(--t);
  }
  .day:hover .add { opacity: 1; }

  .list { flex: 1; min-height: 0; overflow: hidden; display: flex; flex-direction: column; gap: 2px; padding: 2px var(--sp-1) 0; }
  .skeleton { display: block; height: var(--chip-h); flex: none; }

  .more {
    width: 100%; height: var(--chip-h); padding: 0 0.6rem;
    border: 0; border-radius: var(--r-xs); background: transparent;
    font-size: var(--fs-xs); font-weight: 600; color: var(--ink-2); text-align: left; cursor: pointer;
    transition: background-color var(--t), color var(--t);
  }
  .more:hover { background: var(--wash-2); color: var(--ink); }

  /* Неделя: колонки-дни */
  .is-week .head { padding: var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-1); border-bottom: 1px solid var(--line); }
  .is-week .num { height: 2.25rem; padding: 0 var(--sp-2); }
  .is-week .num__d { font-size: var(--fs-2xl); line-height: 1.1; }
  .is-week .num__wd { font-size: var(--fs-sm); }
  .is-week.is-today { background: color-mix(in oklab, var(--signal) 6%, var(--tile)); }
  .is-week .list { overflow-y: auto; gap: var(--sp-2); padding: var(--sp-2); }
  .free { padding: var(--sp-2) var(--sp-1); font-size: var(--fs-xs); color: var(--ink-3); }

  @media (max-width: 47.99rem) {
    .is-week { min-height: 4.5rem; }
    .is-week .list { overflow: visible; }
    .is-week .num__d { font-size: var(--fs-xl); }
    .day:not(.is-week) { cursor: pointer; }
    .day:not(.is-week) .num { pointer-events: none; min-width: 0; padding: 0 0.25rem; }
    .day:not(.is-week) .num__d { font-size: var(--fs-md); }
    ul.list { flex-direction: row; flex-wrap: wrap; align-content: flex-start; gap: 4px; padding: 3px 6px; }
    .day:not(.is-week) .num__wd, .add { display: none; }
    .day:not(.is-week) .skeleton { width: 0.5rem !important; height: 0.5rem; border-radius: 50%; }
    .day:not(.is-week) .list:has(.skeleton) { flex-direction: row; gap: 4px; padding: 3px 6px; }
  }
</style>
