import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");

  return {
    plugins: [react()],
    server: {
      port: parseInt(env.VITE_PORT || "5173", 10),
      host: true,
      proxy: env.VITE_API_PROXY
        ? {
            "/api": {
              target: env.VITE_API_PROXY,
              changeOrigin: true,
              secure: false,
            },
          }
        : undefined,
    },
    preview: {
      port: 4173,
    },
    css: {
      preprocessorOptions: {
        css: {
          charset: false,
        },
      },
    },
  };
});
