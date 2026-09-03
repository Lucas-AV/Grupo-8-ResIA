import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  base: "/static/frontend/",
  build: {
    outDir: "../static/frontend",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/login": "http://127.0.0.1:5000",
      "/logout": "http://127.0.0.1:5000",
      "/callback": "http://127.0.0.1:5000",
    },
  },
});
