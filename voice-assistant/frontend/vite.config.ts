import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../src/api/static",
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    port: 3000,
    proxy: {
      "/health": "http://localhost:8000",
      "/api": "http://localhost:8000",
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
      },
    },
  },
});
