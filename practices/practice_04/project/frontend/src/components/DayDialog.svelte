<script lang="ts">
  import { app } from "../lib/app.svelte";
  import { fmtLong, parseYmd } from "../lib/dates";
  import { capitalize } from "../lib/deadlines";
  import DeadlineCard from "./DeadlineCard.svelte";
  import Icon from "./Icon.svelte";
  import Modal from "./Modal.svelte";

  // Окно дня: все дедлайны дня с «готово», изменить, удалить; добавить на этот день.
  const date = $derived(app.dayDate);
  const list = $derived(date ? (app.byDay.get(date) ?? []) : []);
  const title = $derived(date ? capitalize(fmtLong.format(parseYmd(date)!)) : "");
  let addBtn = $state<HTMLButtonElement>();
</script>

<Modal open={date !== null} {title} onclose={() => (app.dayDate = null)} initialFocus=".card__open, .day-add">
  {#if list.length}
    <ol class="list">
      {#each list as d (d.id)}<DeadlineCard {d} withDelete ondeleted={() => addBtn?.focus()} />{/each}
    </ol>
  {:else}
    <p class="muted">На этот день сроков нет. Добавьте первый.</p>
  {/if}
  <footer class="dialog__foot">
    <span class="dialog__spacer"></span>
    <button type="button" class="btn btn--primary day-add" bind:this={addBtn} onclick={() => app.openDeadline(null, `${date}T23:59`)}>
      <Icon name="plus" />Добавить на этот день
    </button>
  </footer>
</Modal>

<style>
  .list { display: flex; flex-direction: column; gap: var(--sp-2); max-height: 55dvh; overflow-y: auto; margin: 0 calc(-1 * var(--sp-2)); padding: 2px var(--sp-2); }
</style>
