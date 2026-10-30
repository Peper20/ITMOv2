<script lang="ts">
  import type { Deadline } from "../lib/api";
  import { app } from "../lib/app.svelte";
  import { chipTime, describe, isDone, timeOf } from "../lib/deadlines";
  import { decor } from "../lib/decor";

  // Магнитная полоска дедлайна в ячейке месяца; на телефоне — точка-маркер.
  let { d, tab, tall = false }: { d: Deadline; tab: number; tall?: boolean } = $props();
  const time = $derived(isDone(d) ? "✓" : chipTime(d));
  const cat = $derived(d.category_id === null ? undefined : app.categoryById.get(d.category_id));
  const look = $derived(decor(d, app.now, cat));
</script>

<button
  type="button"
  class="chip {look.class}"
  class:is-tall={tall}
  style={look.style}
  tabindex={tab}
  title="{timeOf(d)} {d.title}"
  aria-label={describe(d, app.now, cat?.name)}
  onclick={() => app.openDeadline(d)}
>
  {#if time}<span class="dl__time">{time}</span>{/if}
  <span class="dl__title">{d.title}</span>
  {#if d.priority === 3 && !isDone(d)}<span class="prio" aria-hidden="true">!</span>{/if}
</button>

<style>
  .chip {
    display: flex; align-items: center; gap: 0.375rem;
    width: 100%; height: var(--chip-h); padding: 0 0.25rem 0 0.6rem;
    font-size: var(--fs-sm); line-height: 1;
    white-space: nowrap; overflow: hidden; cursor: pointer;
  }
  .chip:focus-visible { outline-offset: 1px; }
  .dl__time { flex: none; }
  .dl__title { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
  .chip.is-tall { align-items: flex-start; height: var(--chip-h2); padding-top: 0.25rem; padding-bottom: 0.25rem; white-space: normal; }
  .chip.is-tall .dl__time { line-height: 1.35; }
  .chip.is-tall .dl__title {
    display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; line-clamp: 2;
    line-height: 1.25; overflow-wrap: break-word; hyphens: auto;
  }
  .prio { height: 0.9rem; min-width: 0.9rem; }

  @media (max-width: 47.99rem) {
    .chip, .chip.is-tall {
      width: 0.5rem; height: 0.5rem; padding: 0; border-radius: 50%;
      background: var(--cat); pointer-events: none;
    }
    .chip::before, .chip > * { display: none; }
    .chip.is-nocat { background: var(--ink-3); }
    .chip.is-overdue { background: var(--cat); box-shadow: 0 0 0 1.5px var(--tile), 0 0 0 3px var(--alert); }
    .chip.is-done { background: transparent; box-shadow: inset 0 0 0 1.5px var(--ink-3); }
  }
</style>
