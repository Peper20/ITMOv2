<script lang="ts">
  import { app } from "../lib/app.svelte";
  import { WEEKDAYS, WEEKDAYS_FULL, addDays, gridWeeks } from "../lib/dates";
  import DayCell from "./DayCell.svelte";

  // Месяц и неделя — одна сетка дней с разным наполнением; смена периода — сдвиг в сторону перехода.
  const week = $derived(app.view === "week");
  const weeks = $derived(gridWeeks(app.range));
  const month = $derived(addDays(app.range.first, 7).getMonth());
</script>

<main class="cal" class:is-loading={app.slow && app.loaded} aria-busy={app.busy}>
  {#if !week}
    <div class="wds" aria-hidden="true">
      {#each WEEKDAYS as wd, i (wd)}<span class:is-weekend={i >= 5}>{wd}</span>{/each}
    </div>
  {/if}
  {#key app.range.first.getTime()}
    <div
      class="grid"
      class:grid--week={week}
      role="grid"
      aria-label="{app.title}. Стрелки — по дням, Enter — добавить"
      style="--rows: {weeks.length}; --dir: {app.navDir}"
    >
      {#if !week}
        <div class="row visually-hidden" role="row">
          {#each WEEKDAYS_FULL as wd (wd)}<span role="columnheader">{wd}</span>{/each}
        </div>
      {/if}
      {#each weeks as days (days[0].getTime())}
        <div class="row" role="row">
          {#each days as date (date.getTime())}
            <DayCell {date} {week} other={!week && date.getMonth() !== month} />
          {/each}
        </div>
      {/each}
    </div>
  {/key}
</main>

<style>
  .cal { display: flex; flex-direction: column; min-width: 0; min-height: 0; overflow: hidden; transition: opacity var(--t); }
  .cal.is-loading { opacity: 0.55; }

  .wds { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: var(--gap); padding-bottom: var(--gap); }
  .wds span { padding: 0.3rem var(--sp-2); background: var(--tile); color: var(--ink-3); font-size: var(--fs-xs); font-weight: 600; }
  .wds .is-weekend { color: var(--weekend-ink); background: var(--tile-weekend); }

  .grid {
    flex: 1; min-height: 0; display: grid; gap: var(--gap);
    grid-template-rows: repeat(var(--rows, 5), minmax(3.5rem, auto));
    animation: slide 260ms var(--ease);
  }
  @keyframes slide { from { opacity: 0; transform: translateX(calc(var(--dir) * 18px)); } }
  .grid--week { grid-template-rows: minmax(0, 1fr); }
  .row { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: var(--gap); min-height: 0; }

  @media (min-width: 48rem) {
    .grid:not(.grid--week) { grid-template-rows: repeat(var(--rows, 5), minmax(0, 1fr)); }
  }
  @media (max-width: 47.99rem) {
    .grid--week { grid-template-rows: none; }
    .grid--week .row { grid-template-columns: minmax(0, 1fr); }
  }
</style>
