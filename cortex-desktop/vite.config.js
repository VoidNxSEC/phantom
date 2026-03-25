import { defineConfig } from "vite";
import { sveltekit } from "@sveltejs/kit/vite";

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [sveltekit()],

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent Vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      // 3. tell Vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
    proxy: {
      // Forward all backend routes to cortex_api.py on :8087
      "/health":   { target: "http://localhost:8087", changeOrigin: true },
      "/ready":    { target: "http://localhost:8087", changeOrigin: true },
      "/metrics":  { target: "http://localhost:8087", changeOrigin: true },
      "/api":      { target: "http://localhost:8087", changeOrigin: true },
      "/vectors":  { target: "http://localhost:8087", changeOrigin: true },
      "/process":  { target: "http://localhost:8087", changeOrigin: true },
      "/analyze":  { target: "http://localhost:8087", changeOrigin: true },
      "/extract":  { target: "http://localhost:8087", changeOrigin: true },
      "/upload":   { target: "http://localhost:8087", changeOrigin: true },
      "/judge":    { target: "http://localhost:8087", changeOrigin: true },
      "/rag":      { target: "http://localhost:8087", changeOrigin: true },
    },
  },
}));
