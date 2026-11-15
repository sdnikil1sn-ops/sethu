import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development, Vite proxies to the stack published on 127.0.0.1:8080.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8080",
      "/health": "http://127.0.0.1:8080",
      "/auth": "http://127.0.0.1:8080",
    },
  },
  build: { sourcemap: false },
});
