<script lang="ts">
  import { tick, untrack } from "svelte";
  import { ApiError, api, type DeadlineInput, type Priority, type Status } from "../lib/api";
  import { app } from "../lib/app.svelte";
  import { Armed } from "../lib/armed.svelte";
  import { addDays, fmtLong, formatRuDate, maskRuDate, parseLocal, parseRuDate, parseTime, startOfDay, ymd } from "../lib/dates";
  import { PRIORITY_LABEL, STATUS_LABEL, capitalize, isDone, relativeDue } from "../lib/deadlines";
  import Icon from "./Icon.svelte";
  import Modal from "./Modal.svelte";

  // Полное редактирование дедлайна; удаление в два нажатия. Ошибки — у поля (по `field`) или над формой.
  const open = $derived(app.editing !== null);
  const editing = $derived(app.editing?.deadline ?? null);
  const TIMES = ["09:00", "12:00", "18:00", "23:59"];
  const DAYS = [["Сегодня", 0], ["Завтра", 1], ["Через неделю", 7]] as const;
  const dayPreset = (n: number) => formatRuDate(ymd(addDays(startOfDay(app.now), n)));

  let form = $state({ title: "", date: "", time: "", category_id: "", priority: 2 as Priority, status: "todo" as Status, description: "" });
  let errors = $state<Record<string, string>>({});
  let general = $state("");
  let busy = $state(false);
  let formEl = $state<HTMLFormElement>();
  const armed = new Armed();

  // Подпись срока по-русски, независимо от локали браузера: «Четверг, 8 октября, 23:59» и «через 2 дня».
  const due = $derived.by(() => {
    const time = parseTime(form.time);
    const date = parseRuDate(form.date);
    return time && date ? parseLocal(`${date}T${time}`) : null;
  });
  const overdue = $derived(!!due && due < app.now && form.status !== "done");

  // Каждое открытие — заново заполнить форму.
  $effect.pre(() => {
    const e = app.editing;
    if (e) untrack(() => fill(e));
  });

  function fill(e: NonNullable<typeof app.editing>) {
    const d = e.deadline;
    form = {
      title: d?.title ?? "",
      date: formatRuDate(e.due),
      time: e.due.slice(11, 16),
      category_id: d ? String(d.category_id ?? "") : app.presetCategory === null ? "" : String(app.presetCategory),
      priority: d?.priority ?? 2,
      status: d?.status ?? "todo",
      description: d?.description ?? "",
    };
    errors = {};
    general = "";
    armed.reset();
  }

  async function showError(err: ApiError) {
    const name = err.field;
    const el = name ? formEl?.querySelector<HTMLElement>(`[name="${name}"]`) : null;
    if (!el) return void (general = err.message);
    errors = { [name!]: err.message };
    await tick();
    el.focus();
  }

  /** Успех или 404 (уже удалён) — закрыть и обновить, иначе ошибка в форме. */
  async function run(action: () => Promise<unknown>) {
    busy = true;
    errors = {};
    general = "";
    try {
      await action();
    } catch (err) {
      if (!(err instanceof ApiError) || err.status !== 404) {
        busy = false;
        return showError(err instanceof ApiError ? err : new ApiError(0, String(err)));
      }
    }
    busy = false;
    app.editing = null;
    await app.refresh();
  }

  function submit(e: SubmitEvent) {
    e.preventDefault();
    const time = parseTime(form.time);
    if (!form.title.trim()) return showError(new ApiError(400, "Напишите, что нужно сдать.", "title"));
    const date = parseRuDate(form.date);
    if (!date) return showError(new ApiError(400, "Дата — в формате ДД.ММ.ГГГГ, например 08.10.2026.", "due_at"));
    if (!time) return showError(new ApiError(400, "Время — в формате ЧЧ:ММ, например 18:30.", "due_time"));
    const data: DeadlineInput = {
      title: form.title.trim(),
      due_at: `${date}T${time}`,
      category_id: form.category_id ? Number(form.category_id) : null,
      priority: Number(form.priority) as Priority,
      status: form.status,
      description: form.description,
    };
    const id = editing?.id;
    run(() => (id ? api.updateDeadline(id, data) : api.createDeadline(data)));
  }

  function toggleDone() {
    const d = editing;
    if (d) run(() => api.updateDeadline(d.id, { status: isDone(d) ? "todo" : "done" }));
  }

  function remove() {
    const d = editing;
    if (d && armed.press()) run(() => api.deleteDeadline(d.id));
  }

  const err = (name: string) => (errors[name] ? { "aria-invalid": "true" as const, "aria-describedby": `dd-${name}-err` } : {});
</script>

{#snippet fieldError(name: string)}
  {#if errors[name]}<span class="field__error" id="dd-{name}-err">{errors[name]}</span>{/if}
{/snippet}

<Modal {open} title={editing ? "Изменить дедлайн" : "Новый дедлайн"} onclose={() => (app.editing = null)} initialFocus="[name=title]">
  <form class="form" novalidate bind:this={formEl} onsubmit={submit}>
    {#if general}<p class="form-error" role="alert">{general}</p>{/if}

    <label class="field">
      <span class="field__label">Что сдать</span>
      <input class="title" type="text" name="title" maxlength="200" autocomplete="off" placeholder="Лабораторная № 3 по ОС" bind:value={form.title} {...err("title")} />
      {@render fieldError("title")}
    </label>

    <fieldset class="field">
      <legend class="field__label">Срок</legend>
      <div class="when">
        <input type="text" name="due_at" inputmode="numeric" maxlength="10" placeholder="ДД.ММ.ГГГГ" autocomplete="off" aria-label="Дата, ДД.ММ.ГГГГ"
          value={form.date} oninput={(e) => (form.date = e.currentTarget.value = maskRuDate(e.currentTarget.value))} {...err("due_at")} />
        <input class="time" type="text" name="due_time" inputmode="numeric" maxlength="5" placeholder="23:59" aria-label="Время, ЧЧ:ММ" bind:value={form.time} onblur={() => (form.time = parseTime(form.time) ?? form.time)} {...err("due_time")} />
      </div>
      <div class="presets" role="group" aria-label="Быстрый выбор даты">
        {#each DAYS as [label, n] (n)}
          <button type="button" class="preset" aria-pressed={form.date === dayPreset(n)} onclick={() => (form.date = dayPreset(n))}>{label}</button>
        {/each}
      </div>
      <div class="presets" role="group" aria-label="Быстрый выбор времени">
        {#each TIMES as t (t)}
          <button type="button" class="preset" aria-pressed={parseTime(form.time) === t} onclick={() => (form.time = t)}>{t}</button>
        {/each}
      </div>
      {#if due}
        <p class="field__hint caption">{capitalize(fmtLong.format(due))}, {form.time}. <span class:is-alert={overdue}>{capitalize(relativeDue(due, app.now))}</span></p>
      {/if}
      {@render fieldError("due_at")}
      {@render fieldError("due_time")}
    </fieldset>

    <fieldset class="field prio-set">
      <legend class="field__label">Приоритет</legend>
      <div class="segmented">
        {#each [1, 2, 3] as const as p (p)}
          <label class="seg seg--p{p}"><input type="radio" name="priority" value={p} bind:group={form.priority} /><span>{PRIORITY_LABEL[p]}</span></label>
        {/each}
      </div>
      {@render fieldError("priority")}
    </fieldset>

    <div class="field-row">
      <label class="field">
        <span class="field__label">Категория</span>
        <select name="category_id" bind:value={form.category_id} {...err("category_id")}>
          <option value="">Без категории</option>
          {#each app.categories as c (c.id)}<option value={String(c.id)}>{c.name}</option>{/each}
        </select>
        {@render fieldError("category_id")}
      </label>
      <label class="field">
        <span class="field__label">Статус</span>
        <select name="status" bind:value={form.status} {...err("status")}>
          {#each Object.entries(STATUS_LABEL) as [value, label] (value)}<option {value}>{label}</option>{/each}
        </select>
        {@render fieldError("status")}
      </label>
    </div>

    <label class="field">
      <span class="field__label">Заметки</span>
      <textarea name="description" rows="3" maxlength="5000" placeholder="Требования, ссылка на задание, с кем согласовать" bind:value={form.description} {...err("description")}></textarea>
      {@render fieldError("description")}
    </label>

    <footer class="dialog__foot">
      {#if editing}
        <button type="button" class="btn btn--ghost btn--danger" class:is-armed={armed.on} disabled={busy} onclick={remove}>
          <Icon name="trash" />{armed.on ? "Точно удалить?" : "Удалить"}
        </button>
      {/if}
      <span class="dialog__spacer"></span>
      {#if editing}
        <button type="button" class="btn" disabled={busy} onclick={toggleDone}>{isDone(editing) ? "Вернуть в работу" : "Отметить выполненным"}</button>
      {/if}
      <button type="submit" class="btn btn--primary" disabled={busy} aria-busy={busy}>{editing ? "Сохранить" : "Добавить"}</button>
    </footer>
  </form>
</Modal>

<style>
  .form { display: flex; flex-direction: column; gap: var(--sp-4); }
  .title { min-height: 2.75rem; font-size: var(--fs-lg); font-weight: 500; }
  legend { margin-bottom: 0.3rem; }

  .when { display: grid; grid-template-columns: minmax(0, 1fr) 5.5rem; gap: var(--sp-2); }
  .time { text-align: center; font-variant-numeric: tabular-nums; }
  .presets { display: flex; flex-wrap: wrap; gap: var(--sp-1); }
  .preset {
    padding: 0.2rem 0.55rem; border: 1px solid var(--line); border-radius: 999px; background: transparent;
    font-size: var(--fs-xs); color: var(--ink-2); cursor: pointer; transition: background-color var(--t), border-color var(--t), color var(--t);
  }
  .preset:hover { background: var(--wash); color: var(--ink); }
  .preset[aria-pressed="true"] { border-color: var(--ink-2); color: var(--ink); background: var(--wash-2); font-weight: 600; }
  .caption { color: var(--ink-2); }
  .caption .is-alert { color: var(--alert); font-weight: 600; }

  .segmented { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; padding: 3px; border-radius: var(--r-m); background: var(--wash-2); }
  .seg { --p: var(--ink-3); position: relative; }
  .seg--p2 { --p: var(--focus); }
  .seg--p3 { --p: var(--alert); }
  .seg input { position: absolute; inset: 0; opacity: 0; margin: 0; cursor: pointer; }
  .seg span {
    display: flex; align-items: center; justify-content: center; gap: 0.4rem;
    min-height: 2rem; border-radius: var(--r-s); font-size: var(--fs-sm); font-weight: 500; color: var(--ink-2);
    transition: background-color var(--t), color var(--t), box-shadow var(--t);
  }
  .seg span::before { content: ""; width: 0.5rem; height: 0.5rem; border-radius: 50%; background: var(--p); }
  .seg:hover span { color: var(--ink); }
  .seg input:checked + span {
    background: var(--raised); color: var(--ink); font-weight: 600;
    box-shadow: 0 0 0 1.5px color-mix(in oklab, var(--p) 70%, transparent), 0 1px 2px rgb(0 0 0 / 0.12);
  }
  .seg input:focus-visible + span { outline: 2px solid var(--focus); outline-offset: 1px; }
</style>
