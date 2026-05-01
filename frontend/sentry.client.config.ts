import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || process.env.NODE_ENV,
  release: process.env.NEXT_PUBLIC_SENTRY_RELEASE || "1.0.0",
  
  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: parseFloat(process.env.NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE || "0.1"),
  
  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: process.env.NODE_ENV === "development",
  
  // Enable session replay
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  
  integrations: [
    Sentry.replayIntegration({
      maskAllText: true,
      blockAllMedia: true,
    }),
    Sentry.browserTracingIntegration(),
  ],
  
  // Privacy-compliant user tracking
  beforeSend(event, hint) {
    // Anonymize wallet addresses in error messages
    if (event.message) {
      event.message = anonymizeAddress(event.message);
    }
    if (event.exception) {
      event.exception.values?.forEach((value) => {
        if (value.value) {
          value.value = anonymizeAddress(value.value);
        }
      });
    }
    return event;
  },
  
  // Ignore certain errors
  ignoreErrors: [
    // Browser extensions
    "top.GLOBALS",
    "originalCreateNotification",
    "canvas.contentDocument",
    "MyApp_RemoveAllHighlights",
    "atomicFindClose",
    // Network errors that are not actionable
    "NetworkError",
    "Network request failed",
    "Failed to fetch",
  ],
});

function anonymizeAddress(text: string): string {
  // Replace Ethereum addresses with anonymized versions
  const addressRegex = /0x[a-fA-F0-9]{40}/g;
  return text.replace(addressRegex, (match) => {
    return `${match.substring(0, 8)}...${match.substring(36)}`;
  });
}

