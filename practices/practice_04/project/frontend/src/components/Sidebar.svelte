<script lang="ts">
  import type { Deadline } from "../lib/api";
  import { app } from "../lib/app.svelte";
  import { WEEKDAYS, fmtWDM, weekdayIndex, ymd } from "../lib/dates";
  import { countDeadlines, plural, splitUrgent, weekLoad, whenText } from "../lib/deadlines";
  import { decor } from "../lib/decor";

  // Сводка: главный сигнал — просроченные; нагрузка на 7 дней (клик — к дню); списки срочного.
  const groups = $derived(splitUrgent(app.side, app.now));
  const load = $derived(weekLoad(app.side, app.now));
  const peak = $derived(Math.max(3, ...load.map((l) => l.count)));
  const s = $derived(app.stats);
  const look = (d: Deadline) => decor(d, app.now, d.category_id === null ? undefined : app.categoryById.get(d.category_id));

  function goTo(date: Date) {
    app.flashDate = ymd(date);
    app.navigateTo(date);
  }
</script>

{#snippet group(id: string, title: string, items: Deadline[], empty: string)}
  <section class="group" aria-labelledby={id}>
    <h2 class="title" {id}>{title}{#if items.length}<span class="count">{items.length}</span>{/if}</h2>
    <ol class="list">
      {#each items as d (d.id)}
        {@const l = look(d)}
        <li>
          <button type="button" class="item {l.class}" style={l.style} onclick={() => app.openFromSide(d)}>
            <span class="dl__title">{d.title}</span>
            <span class="when">{whenText(d, app.now)}</span>
          </button>
        </li>
      {:else}
        <li class="muted empty">{empty}</li>
      {/each}
    </ol>
  </section>
{/snippet}

<aside class="side" id="side" aria-label="Срочное">
  <section class="summary" aria-live="polite">
    <p class="head" class:is-alert={!!s?.overdue}>
      {#if !s}<span class="skeleton big-skel"></span>
      {:else if s.overdue}<span class="big display">{s.overdue}</span><span>{plural(s.overdue, ["срок просрочен", "срока просрочено", "сроков просрочено"])}</span>
      {:else}<span class="big display">0</span><span>просроченных нет</span>{/if}
    </p>
    <dl class="stats">
      <div><dt>Сегодня</dt><dd class="display">{s?.today ?? "–"}</dd></div>
      <div><dt>За 7 дней</dt><dd class="display">{s?.week ?? "–"}</dd></div>
      <div><dt>Открыто</dt><dd class="display">{s?.open ?? "–"}</dd></div>
    </dl>
  </section>

  <section class="load" aria-labelledby="load-title">
    <h2 class="title" id="load-title">Нагрузка на неделю</h2>
    <ol class="bars">
      {#each load as l, i (l.date.getTime())}
        <li>
          <button type="button" class="bar" class:is-today={i === 0} aria-label="{fmtWDM.format(l.date)}: {l.count ? countDeadlines(l.count) : 'сроков нет'}" title="{fmtWDM.format(l.date)}: {l.count ? countDeadlines(l.count) : 'сроков нет'}" onclick={() => goTo(l.date)}>
            <span class="bar__n">{l.count || ""}</span>
            <span class="bar__fill" style="height: {Math.max(4, (l.count / peak) * 100)}%" class:is-zero={!l.count}></span>
            <span class="bar__wd" class:is-weekend={weekdayIndex(l.date) >= 5}>{i === 0 ? "сег." : WEEKDAYS[weekdayIndex(l.date)]}</span>
          </button>
        </li>
      {/each}
    </ol>
  </section>

  {#if groups.overdue.length}{@render group("side-overdue", "Просрочено", groups.overdue, "")}{/if}
  {@render group("side-week", "Ближайшие 7 дней", groups.soon, "На неделю сроков нет.")}
</aside>

<style>
  .side { display: flex; flex-direction: column; gap: var(--sp-5); padding: var(--sp-4) var(--sp-4) calc(var(--sp-5) + 4rem); background: var(--tile); box-shadow: var(--shadow-tile); }
  .side > :global(*) { flex-shrink: 0; }

  .summary { display: flex; flex-direction: column; gap: var(--sp-3); }
  .head { display: flex; align-items: baseline; gap: var(--sp-2); font-size: var(--fs-sm); font-weight: 500; color: var(--ink-2); }
  .big { font-size: 2.75rem; line-height: 0.9; color: var(--ink); }
  .head.is-alert, .head.is-alert .big { color: var(--alert); }
  .big-skel { width: 8rem; height: 2.5rem; }
  .stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--gap); border-radius: var(--r-s); overflow: hidden; background: var(--line); }
  .stats div { display: flex; flex-direction: column-reverse; gap: 2px; padding: var(--sp-2) var(--sp-3); background: var(--wash); }
  .stats dt { font-size: var(--fs-xs); color: var(--ink-2); }
  .stats dd { font-size: var(--fs-xl); line-height: 1; }

  .title { display: flex; justify-content: space-between; margin-bottom: var(--sp-2); font-size: var(--fs-sm); font-weight: 600; }
  .count { min-width: 1.4rem; padding: 0 0.35rem; border-radius: 999px; background: var(--wash-2); color: var(--ink-2); font-size: var(--fs-xs); text-align: center; line-height: 1.5; }

  .bars { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 2px; height: 5.5rem; }
  .bar {
    display: grid; grid-template-rows: 1rem 1fr auto; justify-items: center; gap: 2px;
    width: 100%; height: 100%; padding: 0 0 2px; border: 0; border-radius: var(--r-s); background: transparent; cursor: pointer;
  }
  .bar:hover { background: var(--wash); }
  .bar__n { font-size: var(--fs-xs); font-weight: 600; color: var(--ink-2); }
  .bar__fill {
    align-self: end; width: 0.875rem; border-radius: 4px 4px 1px 1px;
    background: var(--ink-2); transition: height 300ms var(--ease);
  }
  .bar__fill.is-zero { background: var(--line); }
  .bar:hover .bar__fill:not(.is-zero) { background: var(--ink); }
  .bar__wd { font-size: var(--fs-2xs); color: var(--ink-3); }
  .bar__wd.is-weekend { color: var(--weekend-ink); }
  .bar.is-today .bar__wd { color: var(--ink); font-weight: 700; box-shadow: 0 2px 0 var(--signal); }

  .list { display: flex; flex-direction: column; gap: 3px; }
  .empty { padding: var(--sp-1) 0; }
  .item:not(.is-overdue) { background: transparent; }
  .item:not(.is-overdue):hover { background: var(--wash); }
  .item { display: flex; flex-direction: column; gap: 1px; width: 100%; padding: 0.4rem var(--sp-2) 0.4rem 0.75rem; cursor: pointer; }
  .item .dl__title { font-size: var(--fs-sm); line-height: 1.3; overflow-wrap: anywhere; }
  .when { font-size: var(--fs-xs); color: var(--ink-2); }
  .item.is-overdue .when { color: var(--alert); font-weight: 500; }
</style>
