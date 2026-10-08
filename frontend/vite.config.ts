import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development, API calls go to the local FastAPI server through this proxy, so the
// backend needs no CORS settings. In production, set VITE_API_BASE_URL at build time.
const LOCAL_API = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/analyze": LOCAL_API,
      "/health": LOCAL_API,
      "/next-steps": LOCAL_API,
    },
  },
  preview: {
    proxy: {
      "/analyze": LOCAL_API,
      "/health": LOCAL_API,
      "/next-steps": LOCAL_API,
    },
  },
});
