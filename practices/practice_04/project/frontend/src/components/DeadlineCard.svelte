<script lang="ts">
  import type { Deadline } from "../lib/api";
  import { app } from "../lib/app.svelte";
  import { Armed } from "../lib/armed.svelte";
  import { describe, isDone, isOverdue, STATUS_LABEL, timeOf } from "../lib/deadlines";
  import { decor } from "../lib/decor";
  import Icon from "./Icon.svelte";

  // Карточка дедлайна с «готово» — неделя и окно дня (там же — удаление в два нажатия).
  let { d, tab = 0, withDelete = false, ondeleted }: { d: Deadline; tab?: number; withDelete?: boolean; ondeleted?: () => void } =
    $props();

  const cat = $derived(d.category_id === null ? undefined : app.categoryById.get(d.category_id));
  const look = $derived(decor(d, app.now, cat));
  const meta = $derived(
    [cat?.name, isOverdue(d, app.now) ? "просрочен" : d.status === "todo" ? "" : STATUS_LABEL[d.status].toLowerCase()]
      .filter(Boolean)
      .join(", "),
  );
  const armed = new Armed();
  let busy = false;

  async function toggle(e: Event & { currentTarget: HTMLInputElement }) {
    const box = e.currentTarget;
    if (busy) return void (box.checked = !box.checked);
    busy = true;
    if (!(await app.setDone(d, box.checked))) box.checked = isDone(d);
    busy = false;
  }

  async function del() {
    if (!armed.press() || busy) return;
    busy = true;
    await app.remove(d);
    busy = false;
    ondeleted?.();
  }
</script>

<li class="card {look.class}" style={look.style}>
  <label class="check">
    <input type="checkbox" tabindex={tab} checked={isDone(d)} onchange={toggle} />
    <span class="visually-hidden">Готово: {d.title}</span>
  </label>
  <button type="button" class="open" tabindex={tab} aria-label="Изменить: {describe(d, app.now, cat?.name)}" onclick={() => app.openDeadline(d)}>
    <span class="top">
      <span class="dl__time">{timeOf(d)}</span>
      {#if d.priority === 3 && !isDone(d)}<span class="prio" aria-hidden="true">!</span>{/if}
    </span>
    <span class="dl__title">{d.title}</span>
    {#if meta}<span class="meta">{meta}</span>{/if}
  </button>
  {#if withDelete}
    <button
      type="button"
      class="btn btn--ghost del"
      class:is-armed={armed.on}
      tabindex={tab}
      aria-label={armed.on ? `Точно удалить: ${d.title}?` : `Удалить: ${d.title}`}
      title="Удалить"
      onclick={del}
    >
      {#if armed.on}Точно?{:else}<Icon name="trash" />{/if}
    </button>
  {/if}
</li>

<style>
  /* Флажок и «удалить» — в строке времени, название — на всю ширину карточки */
  .card { display: block; padding: var(--sp-2) var(--sp-2) var(--sp-2) 0.75rem; animation: rise 180ms var(--ease); }
  .check { position: absolute; left: 0.75rem; top: var(--sp-2); display: flex; cursor: pointer; }
  .check input {
    appearance: none; width: 1.125rem; height: 1.125rem; margin: 0;
    border: 1.5px solid var(--line-strong); border-radius: var(--r-xs); background: var(--raised);
    display: grid; place-items: center; cursor: pointer;
    transition: background-color var(--t), border-color var(--t), transform var(--t);
  }
  .check input:hover { border-color: var(--ink-2); }
  .check input:active { transform: scale(0.9); }
  .check input:checked { background: var(--primary); border-color: var(--primary); }
  .check input:checked::after {
    content: ""; width: 0.3rem; height: 0.55rem; margin-top: -2px;
    border: solid var(--on-primary); border-width: 0 2px 2px 0; transform: rotate(45deg);
  }
  .open {
    display: flex; flex-direction: column; gap: 3px; width: 100%; min-width: 0;
    padding: 0; border: 0; background: none; text-align: left; cursor: pointer;
  }
  .top { display: flex; align-items: center; gap: var(--sp-1); min-height: 1.125rem; padding-left: 1.6rem; }
  .card:has(.del) .top { padding-right: 2rem; }
  .dl__title { font-size: var(--fs-sm); line-height: 1.3; overflow-wrap: break-word; hyphens: auto; }
  .open:hover .dl__title { text-decoration: underline; text-decoration-thickness: 1px; text-underline-offset: 2px; }
  .meta { font-size: var(--fs-xs); color: var(--ink-2); }
  .card.is-overdue .meta { color: var(--alert); }
  .del { position: absolute; right: var(--sp-1); top: var(--sp-1); min-height: 1.75rem; min-width: 1.75rem; padding: 0 var(--sp-1); color: var(--ink-3); }
  .del:hover { color: var(--alert); background: var(--alert-wash); }
  .del.is-armed, .del.is-armed:hover { color: var(--tile); background: var(--alert); }
</style>
