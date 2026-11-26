import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// Бэкенд для dev-прокси; бэкенд раздаёт dist/ и ставит immutable на dist/assets/* — assetsDir не меняем.
declare const process: { env: Record<string, string | undefined> }; // без @types/node
const api = process.env.SROKI_API || "http://127.0.0.1:8002";

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: { "/api": { target: api, changeOrigin: true } },
  },
  preview: { host: "127.0.0.1", port: 4173, strictPort: true },
  build: { outDir: "dist", assetsDir: "assets", emptyOutDir: true, target: "es2022" },
  test: { include: ["src/**/*.test.ts"], environment: "node" },
});
