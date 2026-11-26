<script lang="ts">
  import { onMount } from "svelte";
  import { app } from "./lib/app.svelte";
  import { MIN } from "./lib/dates";
  import Banner from "./components/Banner.svelte";
  import Calendar from "./components/Calendar.svelte";
  import CategoriesDialog from "./components/CategoriesDialog.svelte";
  import DayDialog from "./components/DayDialog.svelte";
  import DeadlineDialog from "./components/DeadlineDialog.svelte";
  import Sidebar from "./components/Sidebar.svelte";
  import Toolbar from "./components/Toolbar.svelte";

  // Пустой период: с фильтром — подсказка сбросить его, без фильтра — приглашение добавить срок.
  const hint = $derived.by(() => {
    const q = app.q.trim();
    if (!app.loaded || app.deadlines.length) return null;
    if (q) return { message: `За этот период ничего не найдено по запросу «${q}».`, action: "Сбросить фильтры", run: resetFilters };
    if (app.filterCategory) return { message: "В этой категории за период сроков нет.", action: "Сбросить фильтры", run: resetFilters };
    const period = app.view === "week" ? "На этой неделе" : "В этом месяце";
    return { message: `${period} сроков нет. Нажмите на день, чтобы добавить.`, action: "Новый дедлайн", run: () => app.openDeadline(null) };
  });

  function resetFilters() {
    app.q = "";
    app.filterCategory = "";
    app.refresh();
    document.getElementById("filter-q")?.focus();
  }

  onMount(() => {
    const mq = matchMedia("(max-width: 47.99rem)");
    const onMq = () => (app.mobile = mq.matches);
    onMq();
    mq.addEventListener("change", onMq);
    // Раз в минуту — пересчёт «просрочено» и «сегодня» без запроса.
    const timer = setInterval(() => {
      if (!document.hidden) app.now = new Date();
    }, MIN);
    // Вернулись на вкладку — данные могли устареть.
    const onVisible = () => !document.hidden && app.refresh();
    document.addEventListener("visibilitychange", onVisible);
    app.start();
    return () => {
      mq.removeEventListener("change", onMq);
      clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  });

  // Горячие клавиши: T — сегодня, PageUp/PageDown — период. Не в полях ввода и не в диалогах.
  function onkeydown(e: KeyboardEvent) {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
    const t = e.target as HTMLElement;
    if (document.querySelector("dialog[open]") || t.closest?.("input, select, textarea, [contenteditable]")) return;
    const inCal = !!document.activeElement?.closest(".cal");
    if (e.code === "KeyT" && !e.shiftKey) {
      app.goToday(inCal);
    } else if (e.key === "PageUp" || e.key === "PageDown") {
      e.preventDefault();
      app.shiftPeriod(e.key === "PageUp" ? -1 : 1, inCal);
    }
  }
</script>

<svelte:window {onkeydown} />

<div class="app" class:is-side-closed={!app.sideOpen}>
  <Toolbar />
  {#if app.banner}
    <Banner kind="error" message={app.banner} action="Повторить" onaction={() => app.reloadAll()} />
  {/if}
  <Calendar />
  {#if hint}
    <Banner kind="hint" message={hint.message} action={hint.action} onaction={hint.run} />
  {/if}
  {#if app.sideOpen || app.mobile}
    <Sidebar />
  {/if}
</div>

<DeadlineDialog />
<DayDialog />
<CategoriesDialog />

<style>
  /* Каркас: на десктопе ровно экран, прокручиваются только колонки. */
  .app {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas: "bar" "banner" "cal" "side";
    gap: var(--gap);
    min-height: 100dvh;
    padding-bottom: 5rem; /* место под плавающую кнопку на телефоне */
  }
  .app > :global(.bar) { grid-area: bar; }
  .app > :global(.cal) { grid-area: cal; }
  .app > :global(.side) { grid-area: side; }

  @media (min-width: 48rem) {
    .app {
      height: 100dvh;
      padding: 0;
      grid-template-columns: minmax(0, 1fr) var(--side-w);
      grid-template-rows: auto auto minmax(0, 1fr);
      grid-template-areas: "bar bar" "banner banner" "cal side";
    }
    .app.is-side-closed { grid-template-columns: minmax(0, 1fr); grid-template-areas: "bar" "banner" "cal"; }
    .app > :global(.side) { overflow-y: auto; min-height: 0; }
  }
</style>
