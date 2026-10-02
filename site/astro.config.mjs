// @ts-check
import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://arcanorum.osprey74.com",
  trailingSlash: "ignore",
  build: { format: "directory" },
});
