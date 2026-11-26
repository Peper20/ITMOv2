<script lang="ts">
  // Иконки 16×16 штрихом currentColor; декоративные — подпись даёт кнопка.
  type Name = "prev" | "next" | "close" | "trash" | "panel" | "plus" | "search" | "download" | "tags" | "sun" | "moon" | "auto";
  let { name }: { name: Name } = $props();
</script>

<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
  {#if name === "prev"}<path d="M10 3L5 8l5 5" />
  {:else if name === "next"}<path d="M6 3l5 5-5 5" />
  {:else if name === "close"}<path d="M4 4l8 8M12 4l-8 8" />
  {:else if name === "trash"}<path d="M3 4.5h10M6.5 4.5V3h3v1.5M4.5 4.5l.7 8.5h5.6l.7-8.5" stroke-width="1.4" />
  {:else if name === "plus"}<path d="M8 3v10M3 8h10" stroke-width="1.8" />
  {:else if name === "search"}<circle cx="7" cy="7" r="4.25" /><path d="M10.2 10.2L13.5 13.5" />
  {:else if name === "download"}<path d="M8 2.5v7.5M4.75 7L8 10.25 11.25 7M3 13.5h10" />
  {:else if name === "tags"}<path d="M2.5 2.5h5l6 6-5 5-6-6z" stroke-width="1.4" /><circle cx="5.5" cy="5.5" r="1" fill="currentColor" stroke="none" />
  {:else if name === "sun"}<circle cx="8" cy="8" r="2.75" /><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1 1M11.6 11.6l1 1M3.4 12.6l1-1M11.6 4.4l1-1" stroke-width="1.4" />
  {:else if name === "moon"}<path d="M13 9.5A5.5 5.5 0 0 1 6.5 3a5.5 5.5 0 1 0 6.5 6.5z" />
  {:else if name === "auto"}<circle cx="8" cy="8" r="5.5" /><path d="M8 2.5v11a5.5 5.5 0 0 0 0-11z" fill="currentColor" stroke="none" />
  {:else}<rect x="1.75" y="2.75" width="12.5" height="10.5" rx="1.5" stroke-width="1.4" /><path d="M10 3v10" stroke-width="1.4" />
  {/if}
</svg>
