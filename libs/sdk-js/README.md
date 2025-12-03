# @sentryai/sdk

JavaScript/TypeScript SDK for Sentry for AI.

## Installation

```bash
npm install @sentryai/sdk
```

## Usage

### Initialize

```typescript
import * as sentryai from '@sentryai/sdk';

sentryai.init({
  apiKey: 'sk_test_...',
  projectId: 'proj_demo',
  host: 'https://api.yoursentryai.com', // optional
});
```

### Capture Events

```typescript
// Log messages
sentryai.captureLog('User started chat', 'info');

// Capture errors
try {
  // ... code
} catch (error) {
  sentryai.captureError(error);
}

// Track LLM usage
sentryai.captureLLMUsage('gpt-4', 150, 300, 0.05);

// Track model responses
sentryai.captureModelResponse(
  'gpt-4',
  1250, // latency in ms
  true, // success
  { inputTokens: 150, outputTokens: 300 },
  'What is AI?', // optional prompt
  'AI is...' // optional response
);
```

### Class-based API

```typescript
import { SentryAI } from '@sentryai/sdk';

const client = SentryAI.init({
  apiKey: 'sk_test_...',
  projectId: 'proj_demo',
});

client.captureLog('Hello!');
```

## Features

- Non-blocking event queue
- Auto-batching (sends every 10 events or 5 seconds)
- Graceful shutdown with flush
- Works in Node.js and browsers
- TypeScript support
