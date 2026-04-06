"use client";

import { useEffect } from "react";

const POSTHOG_KEY = "phc_6iC8kWZD8EzWetkwaYvvamfLKo2PrQnLK3y7ADCSz7r";
const POSTHOG_HOST = "https://eu.i.posthog.com";

export default function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // Dynamically load PostHog to avoid SSG issues
    import("posthog-js").then((posthog) => {
      posthog.default.init(POSTHOG_KEY, {
        api_host: POSTHOG_HOST,
        capture_pageview: true,
        capture_pageleave: true,
        persistence: "localStorage",
        autocapture: false,
      });
      // Expose to window for use in event helpers
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (window as any).posthog = posthog.default;
    }).catch(() => {
      // Analytics unavailable — fail silently
    });
  }, []);

  return <>{children}</>;
}
