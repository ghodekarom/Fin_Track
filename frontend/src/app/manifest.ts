import { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "FinTrack — Personal Expense Tracker",
    short_name: "FinTrack",
    description: "Track monthly expenses, manage custom categories, and monitor active budgets with AI-powered insights.",
    start_url: "/dashboard",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#09090b",
    theme_color: "#09090b",
    icons: [
      {
        src: "/icon-192x192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/icon-512x512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/apple-touch-icon.png",
        sizes: "180x180",
        type: "image/png",
      },
    ],
    shortcuts: [
      {
        name: "Log Expense",
        short_name: "Add",
        description: "Quickly record a new expense",
        url: "/expenses/new",
        icons: [{ src: "/icon-192x192.png", sizes: "192x192" }],
      },
      {
        name: "Dashboard",
        short_name: "Dashboard",
        description: "View financial overview & AI insights",
        url: "/dashboard",
        icons: [{ src: "/icon-192x192.png", sizes: "192x192" }],
      },
    ],
  };
}

