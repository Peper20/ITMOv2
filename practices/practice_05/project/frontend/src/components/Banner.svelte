<script lang="ts">
  // Полоса ошибки связи/сервера с повтором и подсказка «ничего не найдено» с сбросом фильтров.
  let { kind, message, action, onaction }: { kind: "error" | "hint"; message: string; action: string; onaction: () => void } = $props();
</script>

<div class="banner banner--{kind}" role={kind === "error" ? "alert" : "status"}>
  <p>{message}</p>
  <button type="button" class="btn" onclick={onaction}>{action}</button>
</div>

<style>
  .banner { display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-2) var(--sp-4); font-size: var(--fs-sm); }
  .banner p { flex: 1; }
  .banner--error { grid-area: banner; background: var(--alert-wash); color: var(--alert); font-weight: 500; box-shadow: inset 4px 0 0 var(--alert); }
  .banner--hint {
    grid-area: cal; z-index: 3; align-self: end; justify-self: center; max-width: calc(100% - 2rem); margin: var(--sp-4);
    padding: var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-4); border-radius: var(--r-m);
    background: var(--primary); color: var(--on-primary);
    box-shadow: 0 12px 32px -10px rgb(0 0 0 / 0.5); animation: rise 220ms var(--ease);
  }
  .banner--hint .btn { background: transparent; color: inherit; border-color: color-mix(in oklab, var(--on-primary) 40%, transparent); }
  .banner--hint .btn:hover { background: color-mix(in oklab, var(--on-primary) 14%, transparent); }
</style>
