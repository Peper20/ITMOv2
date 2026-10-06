<script lang="ts">
  import { tick, untrack } from "svelte";
  import { ApiError, api, type Kind } from "../lib/api";
  import { app } from "../lib/app.svelte";
  import { KIND_LABEL } from "../lib/categories";
  import CategoryRow from "./CategoryRow.svelte";
  import Modal from "./Modal.svelte";

  // Управление категориями: список с правкой на месте и форма создания.
  let name = $state("");
  let kind = $state<Kind>("study");
  let color = $state("#2f6fd0");
  let errors = $state<Record<string, string>>({});
  let general = $state("");
  let busy = $state(false);
  let nameEl = $state<HTMLInputElement>();

  // При открытии — свежие open_count.
  $effect(() => {
    if (!app.categoriesOpen) return;
    untrack(() => {
      errors = {};
      general = "";
      app.loadCategories().catch((err: Error) => (general = err.message));
    });
  });

  function close() {
    app.categoriesOpen = false;
    app.refresh(); // могли смениться имена, цвета, удалиться категории
  }

  async function create(e: SubmitEvent) {
    e.preventDefault();
    errors = {};
    general = "";
    const data = { name: name.trim(), kind, color };
    if (!data.name) {
      errors = { name: "Введите название категории." };
      return nameEl?.focus();
    }
    busy = true;
    try {
      await api.createCategory(data);
      name = "";
      await app.loadCategories();
    } catch (err) {
      const e = err instanceof ApiError ? err : new ApiError(0, String(err));
      if (e.field && ["name", "kind", "color"].includes(e.field)) errors = { [e.field]: e.message };
      else general = e.message;
    } finally {
      busy = false;
      await tick();
      nameEl?.focus();
    }
  }

  async function deleted() {
    nameEl?.focus(); // строка исчезнет — фокус в форму создания
    await app.reloadAll();
  }
</script>

<Modal open={app.categoriesOpen} title="Категории" onclose={close} initialFocus="[name=new-name]">
  <ul class="list">
    {#each app.categories as c (c.id)}
      <CategoryRow {c} ondeleted={deleted} />
    {:else}
      <li class="muted">Категорий пока нет. Заведите курс или проект ниже.</li>
    {/each}
  </ul>

  <form class="create" novalidate onsubmit={create} aria-labelledby="cat-new-title">
    <h3 class="create__title" id="cat-new-title">Новая категория</h3>
    {#if general}<p class="form-error" role="alert">{general}</p>{/if}
    <div class="field-row create__row">
      <label class="field">
        <span class="field__label">Название</span>
        <input
          type="text"
          name="new-name"
          maxlength="60"
          autocomplete="off"
          placeholder="Матанализ"
          bind:value={name}
          bind:this={nameEl}
          aria-invalid={errors.name ? "true" : undefined}
          aria-describedby={errors.name ? "cat-name-err" : undefined}
        />
        {#if errors.name}<span class="field__error" id="cat-name-err">{errors.name}</span>{/if}
      </label>
      <label class="field">
        <span class="field__label">Тип</span>
        <select bind:value={kind}>
          {#each Object.entries(KIND_LABEL) as [value, label] (value)}<option {value}>{label}</option>{/each}
        </select>
        {#if errors.kind}<span class="field__error">{errors.kind}</span>{/if}
      </label>
      <label class="field">
        <span class="field__label">Цвет</span>
        <input type="color" bind:value={color} />
        {#if errors.color}<span class="field__error">{errors.color}</span>{/if}
      </label>
    </div>
    <footer class="dialog__foot">
      <span class="dialog__spacer"></span>
      <button type="submit" class="btn btn--primary" disabled={busy}>Добавить категорию</button>
    </footer>
  </form>
</Modal>

<style>
  .list { display: flex; flex-direction: column; gap: var(--sp-1); max-height: 45dvh; overflow-y: auto; }
  .create { display: flex; flex-direction: column; gap: var(--sp-3); padding-top: var(--sp-4); border-top: 1px solid var(--line); }
  .create__title { font-size: var(--fs-sm); font-weight: 600; }
  @media (min-width: 30rem) {
    .create__row { grid-template-columns: minmax(0, 1fr) 8rem auto; }
  }
</style>
