<script lang="ts">
  import { app } from "../lib/app.svelte";
  import Icon from "./Icon.svelte";

  // Сообщение о следующем экземпляре повтора: озвучивается вежливо, фокус не забирает,
  // само закрывается через 8 с (пауза, пока на нём курсор или фокус), Esc — закрыть.
  const DELAY = 8000;
  let paused = $state(false);
  let hovered = false;
  let focused = false;
  const sync = () => (paused = hovered || focused);

  $effect(() => {
    const n = app.notice;
    if (!n || paused) return;
    const timer = setTimeout(() => app.notice === n && (app.notice = null), DELAY);
    return () => clearTimeout(timer);
  });

  function onkeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && app.notice && !document.querySelector("dialog[open]")) app.notice = null;
  }
</script>

<svelte:window {onkeydown} />

<!-- Живая область существует всегда, иначе диктор может не озвучить первое сообщение. -->
<div class="live" role="status" aria-live="polite">
  {#if app.notice}
    <div
      class="notice"
      role="group"
      aria-label="Следующий дедлайн"
      onmouseenter={() => ((hovered = true), sync())}
      onmouseleave={() => ((hovered = false), sync())}
      onfocusin={() => ((focused = true), sync())}
      onfocusout={() => ((focused = false), sync())}
    >
      <Icon name="repeat" />
      <p>{app.notice.text}</p>
      {#if app.notice.date}<button type="button" class="btn show" onclick={() => app.showNotice()}>Показать</button>{/if}
      <button type="button" class="btn btn--ghost btn--icon close" aria-label="Закрыть" title="Закрыть" onclick={() => (app.notice = null)}>
        <Icon name="close" />
      </button>
    </div>
  {/if}
</div>

<style>
  .live { position: fixed; z-index: 6; left: var(--sp-4); bottom: calc(var(--sp-4) + 3.75rem + env(safe-area-inset-bottom)); max-width: min(26rem, calc(100% - 2 * var(--sp-4))); }
  .notice {
    display: flex; align-items: center; gap: var(--sp-2);
    padding: var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-3); border-radius: var(--r-m);
    background: var(--primary); color: var(--on-primary); font-size: var(--fs-sm);
    box-shadow: 0 12px 32px -10px rgb(0 0 0 / 0.5); animation: rise 220ms var(--ease);
  }
  .notice p { flex: 1; min-width: 0; }
  .show { background: transparent; color: inherit; border-color: color-mix(in oklab, var(--on-primary) 40%, transparent); }
  .show:hover, .close:hover { background: color-mix(in oklab, var(--on-primary) 14%, transparent); }
  .close { color: inherit; }
  @media (min-width: 48rem) { .live { bottom: var(--sp-4); } }
</style>
