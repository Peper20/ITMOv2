<script lang="ts">
  import { app } from "../lib/app.svelte";
  import Icon from "./Icon.svelte";

  // Шапка: главное — период и навигация; затем вид и фильтры; «Новый дедлайн»; вторичные иконки.
  const week = $derived(app.view === "week");
  const THEME = {
    system: { icon: "auto", label: "системная", next: "светлую" },
    light: { icon: "sun", label: "светлая", next: "тёмную" },
    dark: { icon: "moon", label: "тёмная", next: "системную" },
  } as const;
  const theme = $derived(THEME[app.theme]);
  let timer: ReturnType<typeof setTimeout> | undefined;

  function search() {
    clearTimeout(timer);
    timer = setTimeout(() => app.refresh(), 300);
  }
</script>

<header class="bar">
  <h1 class="brand display">Сроки</h1>

  <nav class="nav" aria-label="Период">
    <button type="button" class="btn btn--icon btn--ghost" aria-label={week ? "Предыдущая неделя" : "Предыдущий месяц"} onclick={() => app.shiftPeriod(-1)}>
      <Icon name="prev" />
    </button>
    <h2 class="period display" aria-live="polite">{app.title}</h2>
    <button type="button" class="btn btn--icon btn--ghost" aria-label={week ? "Следующая неделя" : "Следующий месяц"} onclick={() => app.shiftPeriod(1)}>
      <Icon name="next" />
    </button>
    <button type="button" class="btn today" onclick={() => app.goToday()}>Сегодня</button>
  </nav>

  <div class="views" role="group" aria-label="Вид календаря">
    <button type="button" aria-pressed={!week} onclick={() => app.setView("month")}>Месяц</button>
    <button type="button" aria-pressed={week} onclick={() => app.setView("week")}>Неделя</button>
  </div>

  <form
    class="filters"
    role="search"
    aria-label="Фильтры"
    onsubmit={(e) => {
      e.preventDefault();
      clearTimeout(timer);
      app.refresh();
    }}
  >
    <label class="filters__cat">
      <span class="visually-hidden">Категория</span>
      <select bind:value={app.filterCategory} class:is-set={app.filterCategory !== ""} onchange={() => app.refresh()}>
        <option value="">Все категории</option>
        <option value="none">Без категории</option>
        {#each app.categories as c (c.id)}<option value={String(c.id)}>{c.name}</option>{/each}
      </select>
    </label>
    <label class="filters__q">
      <span class="visually-hidden">Поиск</span>
      <Icon name="search" />
      <input id="filter-q" type="search" placeholder="Поиск по сроку" autocomplete="off" bind:value={app.q} oninput={search} />
    </label>
  </form>

  <button type="button" class="btn btn--primary new" id="new-deadline" onclick={() => app.openDeadline(null)}>
    <Icon name="plus" /><span>Новый дедлайн</span>
  </button>

  <div class="tools" role="group" aria-label="Ещё">
    <button type="button" class="btn btn--ghost btn--icon" title="Категории" aria-label="Категории" onclick={() => (app.categoriesOpen = true)}>
      <Icon name="tags" />
    </button>
    <a class="btn btn--ghost btn--icon" href={app.exportHref} download="sroki.ics" title="Экспорт .ics: невыполненные по текущим фильтрам" aria-label="Экспорт .ics">
      <Icon name="download" />
    </a>
    <button type="button" class="btn btn--ghost btn--icon" title="Тема: {theme.label}" aria-label="Тема: {theme.label}. Переключить на {theme.next}" onclick={() => app.cycleTheme()}>
      <Icon name={theme.icon} />
    </button>
    <button type="button" class="btn btn--ghost btn--icon side-toggle" class:is-on={app.sideOpen} aria-controls="side" aria-expanded={app.sideOpen} title="Панель срочного" aria-label="Панель срочного" onclick={() => app.toggleSide()}>
      <Icon name="panel" />
    </button>
  </div>
</header>

<style>
  .bar {
    display: grid; align-items: center; gap: var(--sp-2);
    grid-template-columns: auto minmax(0, 1fr);
    grid-template-areas: "nav nav" "views tools" "filters filters";
    padding: var(--sp-2) var(--sp-3) var(--sp-3);
    background: var(--tile);
    box-shadow: var(--shadow-tile);
  }
  .brand { display: none; }
  .nav { grid-area: nav; display: flex; align-items: center; gap: var(--sp-1); min-width: 0; }
  .period { flex: 1; min-width: 0; font-size: var(--fs-xl); line-height: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: center; }
  .today { margin-left: var(--sp-1); }

  .views { grid-area: views; display: inline-flex; padding: 3px; gap: 2px; border-radius: var(--r-m); background: var(--wash-2); }
  .views button {
    min-height: 1.875rem; padding: 0 var(--sp-3);
    border: 0; border-radius: var(--r-s); background: transparent;
    font-size: var(--fs-sm); font-weight: 500; color: var(--ink-2); cursor: pointer;
    transition: background-color var(--t), color var(--t), box-shadow var(--t);
  }
  .views button:hover { color: var(--ink); }
  .views button[aria-pressed="true"] { background: var(--raised); color: var(--ink); font-weight: 600; box-shadow: 0 1px 2px rgb(0 0 0 / 0.15), 0 0 0 1px var(--line); }

  .filters { grid-area: filters; display: flex; gap: var(--sp-2); min-width: 0; }
  .filters__cat { flex: 0 1 10.5rem; min-width: 0; }
  .filters__cat select.is-set { border-color: var(--focus); color: var(--focus); font-weight: 500; }
  .filters__q { position: relative; flex: 1 1 12rem; min-width: 0; color: var(--ink-3); }
  .filters__q :global(svg) { position: absolute; left: 0.625rem; top: 50%; transform: translateY(-50%); pointer-events: none; }
  .filters__q input { padding-left: 2rem; }

  .tools { grid-area: tools; justify-self: end; display: flex; gap: 2px; }
  .side-toggle { display: none; }
  .side-toggle.is-on { color: var(--ink); background: var(--wash); }

  /* Телефон: «Новый дедлайн» — плавающая кнопка внизу */
  .new {
    position: fixed; z-index: 5; right: var(--sp-4); bottom: calc(var(--sp-4) + env(safe-area-inset-bottom));
    min-height: 3rem; padding: 0 var(--sp-4); border-radius: 999px;
    box-shadow: 0 10px 24px -8px rgb(0 0 0 / 0.45);
  }

  @media (min-width: 48rem) {
    .bar { display: flex; flex-wrap: wrap; gap: var(--sp-2) var(--sp-3); padding: var(--sp-2) var(--sp-4); }
    .brand { display: block; font-size: var(--fs-lg); padding-right: var(--sp-3); margin-right: var(--sp-1); border-right: 1px solid var(--line); line-height: 1.6; }
    .period { flex: none; min-width: 9.5em; font-size: var(--fs-2xl); text-align: left; padding: 0 var(--sp-1); }
    .filters { flex: 1 1 18rem; max-width: 30rem; }
    .new { position: static; min-height: var(--control-h); padding: 0 var(--sp-3) 0 var(--sp-2); border-radius: var(--r-s); box-shadow: none; margin-left: auto; }
    .side-toggle { display: inline-flex; }
    .tools { padding-left: var(--sp-2); border-left: 1px solid var(--line); }
  }
</style>
