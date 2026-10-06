<script lang="ts">
  import { api, type Category, type Kind } from "../lib/api";
  import { app } from "../lib/app.svelte";
  import { Armed } from "../lib/armed.svelte";
  import { KIND_LABEL, deleteWarning, openCountText } from "../lib/categories";
  import Icon from "./Icon.svelte";

  // Строка категории: правка на месте (каждое изменение — PATCH), удаление в два нажатия.
  let { c, ondeleted }: { c: Category; ondeleted: () => void } = $props();
  let note = $state("");
  let isError = $state(false);
  let busy = $state(false);
  const armed = new Armed(5000);
  const shown = $derived(armed.on ? deleteWarning(c) : note || openCountText(c));
  const noteId = $derived(`cat-note-${c.id}`);

  async function save(e: Event & { currentTarget: HTMLInputElement | HTMLSelectElement }) {
    const input = e.currentTarget;
    const field = input.name as "name" | "color" | "kind";
    const value = field === "name" ? input.value.trim() : input.value;
    if (value === c[field]) return;
    if (!value) {
      input.value = c[field];
      [note, isError] = ["Название не может быть пустым.", true];
      return;
    }
    try {
      const updated = await api.updateCategory(c.id, { [field]: value as Kind });
      app.applyCategory(updated);
      [note, isError] = [`Сохранено. ${openCountText(updated)}`, false];
    } catch (err) {
      input.value = c[field];
      [note, isError] = [(err as Error).message, true];
    }
  }

  async function remove() {
    if (!armed.press()) return;
    busy = true;
    try {
      await api.deleteCategory(c.id);
    } catch (err) {
      if ((err as { status?: number }).status !== 404) {
        busy = false;
        [note, isError] = [(err as Error).message, true];
        return;
      }
    }
    ondeleted();
  }
</script>

<li class="row">
  <form class="row__form" novalidate onsubmit={(e) => { e.preventDefault(); (e.currentTarget.elements.namedItem("name") as HTMLInputElement).blur(); }}>
    <label>
      <span class="visually-hidden">Цвет категории {c.name}</span>
      <input type="color" name="color" value={c.color} onchange={save} />
    </label>
    <label>
      <span class="visually-hidden">Название</span>
      <input type="text" name="name" maxlength="60" autocomplete="off" value={c.name} onchange={save} aria-describedby={noteId} />
    </label>
    <label>
      <span class="visually-hidden">Тип</span>
      <select name="kind" value={c.kind} onchange={save}>
        {#each Object.entries(KIND_LABEL) as [value, label] (value)}<option {value}>{label}</option>{/each}
      </select>
    </label>
    <button type="button" class="btn btn--icon btn--ghost" class:is-armed={armed.on} disabled={busy} aria-label="Удалить категорию {c.name}" onclick={remove}>
      <Icon name="trash" />
    </button>
  </form>
  <p class="row__note" class:is-error={isError || armed.on} id={noteId} aria-live="polite">{shown}</p>
</li>

<style>
  .row { padding: var(--sp-1) 0; border-bottom: 1px solid var(--line); }
  .row__form { display: grid; grid-template-columns: auto minmax(0, 1fr) 7.5rem auto; gap: var(--sp-2); align-items: center; }
  .row :global(input[type="color"]) { border-radius: 50%; width: var(--control-h); }
  .row__note { padding-left: 3rem; font-size: var(--fs-xs); color: var(--ink-3); }
  .row__note.is-error { color: var(--alert); }
</style>
