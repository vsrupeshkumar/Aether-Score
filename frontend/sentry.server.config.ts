import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.SENTRY_DSN_FRONTEND || process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.SENTRY_ENVIRONMENT || process.env.NODE_ENV,
  release: process.env.SENTRY_RELEASE || "1.0.0",
  
  // Adjust this value in production, or use tracesSampler for greater control
  tracesSampleRate: parseFloat(process.env.SENTRY_TRACES_SAMPLE_RATE || "0.1"),
  
  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: process.env.NODE_ENV === "development",
  
  integrations: [
    Sentry.prismaIntegration(),
    Sentry.httpIntegration(),
  ],
  
  // Privacy-compliant user tracking
  beforeSend(event, hint) {
    // Anonymize wallet addresses
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
    "ECONNREFUSED",
    "ENOTFOUND",
  ],
});

function anonymizeAddress(text: string): string {
  // Replace Ethereum addresses with anonymized versions
  const addressRegex = /0x[a-fA-F0-9]{40}/g;
  return text.replace(addressRegex, (match) => {
    return `${match.substring(0, 8)}...${match.substring(36)}`;
  });
}

