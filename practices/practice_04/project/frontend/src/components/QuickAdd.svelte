<script lang="ts">
  import { app } from "../lib/app.svelte";
  import { fmtLong, parseYmd } from "../lib/dates";

  // Быстрое добавление в ячейке: Enter — создать на этот день в 23:59, Esc — отмена.
  const qa = $derived(app.qa!);
  const errId = $derived(`qa-err-${qa.date}`);

  function focusOnMount(node: HTMLInputElement) {
    node.focus();
  }

  // Ушли из пустого поля — отмена; с текстом поле остаётся, чтобы не терять набранное.
  function onfocusout(e: FocusEvent & { currentTarget: HTMLFormElement }) {
    if (app.qa && !app.qa.text.trim() && !e.currentTarget.contains(e.relatedTarget as Node | null)) app.closeQuickAdd();
  }

  function onkeydown(e: KeyboardEvent) {
    if (e.key !== "Escape") return;
    e.preventDefault();
    e.stopPropagation();
    app.closeQuickAdd(true);
  }
</script>

<form
  class="qa"
  novalidate
  {onfocusout}
  onsubmit={(e) => {
    e.preventDefault();
    app.submitQuickAdd();
  }}
>
  <input
    type="text"
    maxlength="200"
    autocomplete="off"
    placeholder="Что сдать? Enter — добавить"
    aria-label="Новый дедлайн на {fmtLong.format(parseYmd(qa.date)!)}, 23:59"
    aria-invalid={qa.error ? "true" : undefined}
    aria-describedby={qa.error ? errId : undefined}
    bind:value={qa.text}
    oninput={() => (qa.error = "")}
    {onkeydown}
    use:focusOnMount
  />
  {#if qa.error}<p class="qa__err" id={errId}>{qa.error}</p>{/if}
</form>

<style>
  .qa {
    position: absolute; z-index: 2; left: 2px; right: 2px; bottom: 2px;
    padding: 3px; border-radius: var(--r-s);
    background: var(--raised);
    box-shadow: 0 0 0 2px var(--focus), 0 10px 24px -8px rgb(0 0 0 / 0.4);
    cursor: auto; animation: rise 160ms var(--ease);
  }
  .qa input { min-height: 1.875rem; border-color: transparent; font-size: var(--fs-sm); box-shadow: none !important; }
  .qa__err { padding: 2px var(--sp-1); font-size: var(--fs-xs); color: var(--alert); }
</style>
