import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [
    tsconfigPaths(),
    // Exclude react-pdf / pdfjs from the React transform — they rely on
    // web workers that break in the jsdom test environment.
    react({ exclude: [/\/pdf\//, /react-pdf/, /pdfjs-dist/] }),
  ],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // Only pick up our own test files, never node_modules.
    include: ["**/*.test.{ts,tsx}"],
    exclude: ["node_modules", ".next"],
  },
});
