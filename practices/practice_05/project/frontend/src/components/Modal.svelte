<script lang="ts">
  import { tick, type Snippet } from "svelte";
  import Icon from "./Icon.svelte";

  // Обёртка над <dialog>: открывается по `open`, закрывается Esc/крестиком/кликом по фону,
  // возвращает фокус тому, кто открыл (или дню-курсору, если открывший исчез).
  let {
    open,
    title,
    onclose,
    initialFocus = "",
    children,
  }: { open: boolean; title: string; onclose: () => void; initialFocus?: string; children: Snippet } = $props();

  let dialog: HTMLDialogElement;
  let opener: HTMLElement | null = null;
  const id = `dlg-${Math.random().toString(36).slice(2, 8)}`;

  // Закрытие управляется состоянием: крестик, фон и Esc зовут onclose(), а dialog.close() делает эффект.
  // На событие `close` не полагаемся: браузер может доставить его с задержкой (фоновая вкладка).
  $effect(() => {
    if (open && !dialog.open) {
      opener = document.activeElement as HTMLElement | null;
      dialog.showModal();
      if (initialFocus) dialog.querySelector<HTMLElement>(initialFocus)?.focus();
    } else if (!open && dialog.open) {
      dialog.close();
      tick().then(restoreFocus); // после перерисовки, вызванной закрытием
    }
  });

  function restoreFocus() {
    if (opener?.isConnected && !opener.closest("[hidden]")) return opener.focus();
    const target = document.querySelector<HTMLElement>('[data-day][tabindex="0"]') ?? document.getElementById("new-deadline");
    target?.focus();
  }

  function oncancel(e: Event) {
    e.preventDefault();
    onclose();
  }

  // Запасной путь: диалог закрыли в обход состояния (Esc без события cancel и т. п.).
  function handleClose() {
    if (!open || dialog.open) return; // запоздавшее событие прошлого открытия
    onclose();
    tick().then(restoreFocus);
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
<dialog
  class="dialog"
  bind:this={dialog}
  aria-labelledby={id}
  onclose={handleClose}
  {oncancel}
  onclick={(e) => e.target === dialog && onclose()}
>
  {#if open}
    <div class="dialog__body">
      <header class="dialog__head">
        <h2 {id}>{title}</h2>
        <button type="button" class="btn btn--icon btn--ghost" aria-label="Закрыть" onclick={onclose}>
          <Icon name="close" />
        </button>
      </header>
      {@render children()}
    </div>
  {/if}
</dialog>

<style>
  .dialog {
    width: min(36rem, calc(100vw - 2rem)); /* не шире вьюпорта минус поля на любой ширине */
    max-width: calc(100vw - 2rem);
    max-height: calc(100dvh - 2rem);
    overflow-x: hidden;
    padding: 0;
    border: 0;
    border-radius: var(--r-l);
    background: var(--tile);
    color: var(--ink);
    box-shadow: var(--shadow-pop);
  }
  .dialog::backdrop { background: var(--backdrop); }
  .dialog[open] { animation: dialog-in 200ms var(--ease); }
  .dialog[open]::backdrop { animation: fade 200ms var(--ease); }
  @keyframes dialog-in { from { opacity: 0; transform: translateY(8px) scale(0.98); } }
  @keyframes fade { from { opacity: 0; } }

  /* Телефон: окно — лист снизу */
  @media (max-width: 30rem) {
    .dialog { width: 100vw; max-width: 100vw; max-height: 92dvh; margin: auto 0 0; border-radius: var(--r-l) var(--r-l) 0 0; }
    .dialog :global(.dialog__foot) { border-radius: 0; padding-bottom: calc(var(--sp-3) + env(safe-area-inset-bottom)); }
    .dialog :global(.dialog__foot .btn) { flex: 1 1 auto; }
    .dialog :global(.dialog__spacer) { display: none; }
    .dialog[open] { animation-name: sheet-in; }
    @keyframes sheet-in { from { transform: translateY(40px); opacity: 0; } }
  }
</style>
