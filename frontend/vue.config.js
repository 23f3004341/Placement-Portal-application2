const { defineConfig } = require("@vue/cli-service");

const backendTarget = process.env.VUE_APP_BACKEND_URL || "http://127.0.0.1:5002";

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    watchFiles: {
      paths: ["src/**/*", "public/**/*"],
      options: {
        ignored: ["**/node_modules/**", "**/.node_modules_corrupt_*/**"],
      },
    },
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/service-worker.js": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/static/uploads": {
        target: backendTarget,
        changeOrigin: true,
      },
      "/static/exports": {
        target: backendTarget,
        changeOrigin: true,
      },
    },
  },
});
