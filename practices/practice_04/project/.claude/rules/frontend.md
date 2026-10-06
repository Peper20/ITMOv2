---
paths:
  - "frontend/**"
---

# Фронтенд

- Svelte 5 (руны) + Vite, TypeScript. Зависимости ставятся через npm (`frontend/package.json`,
  `package-lock.json` коммитится). Набор зависимостей минимальный: svelte, vite,
  @sveltejs/vite-plugin-svelte, typescript, svelte-check, vitest, а также шрифты
  `@fontsource/*` с лицензией OFL (не больше двух семейств, только нужные начертания и
  подмножества latin + cyrillic; файлы попадают в `dist/`). Любую другую — только с
  обоснованием в отчёте оркестратору. UI-киты, CSS-фреймворки и SvelteKit не используем.
- В рантайме никаких внешних запросов: без CDN, шрифтов из сети, аналитики. Ассеты — локально.
  При создании или переработке интерфейса загружай скил `frontend-design`.
- Структура: `frontend/src/lib/api.ts` — единственное место работы с API (типы по контракту
  из `docs/PLAN.md`), `frontend/src/lib/*.ts` — чистая логика (даты, группировка) с тестами
  vitest, `frontend/src/components/*.svelte` — компоненты, глобальные токены — `src/app.css`.
- Пользовательский ввод — только через обычную интерполяцию `{...}`, никаких `{@html}`.
- Разметка семантическая (`header`, `main`, `form`, `label`), адаптивная вёрстка (mobile-first).
- Команды (из `frontend/`): `npm run dev` (Vite, прокси `/api` на бэкенд), `npm run build`
  (→ `frontend/dist`, его раздаёт бэкенд), `npm run check` (svelte-check), `npm test` (vitest).
- Перед отчётом: `npm run check`, `npm test` и `npm run build` без ошибок.
