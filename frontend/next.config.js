const withPWA = require("@ducanh2912/next-pwa").default({
  dest: "public",
  disable: process.env.NODE_ENV === "development" && process.env.ENABLE_PWA_DEV !== "true",
  register: true,
  skipWaiting: true,
  fallbacks: {
    document: "/offline",
  },
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  /* We can add other standard settings if needed */
};

module.exports = withPWA(nextConfig);
