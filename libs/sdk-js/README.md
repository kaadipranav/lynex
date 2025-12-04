# @lynex/sdk

JavaScript/TypeScript SDK for Lynex.

## Installation

```bash
npm install @lynex/sdk
```

## Usage

### Initialize

```typescript
import * as lynex from '@lynex/sdk';

lynex.init({
  apiKey: 'sk_test_...',
  projectId: 'proj_demo',
  host: 'https://api.yourlynex.com', // optional
});
```

### Capture Events

```typescript
// Log messages
lynex.captureLog('User started chat', 'info');

// Capture errors
try {
  // ... code
} catch (error) {
  lynex.captureError(error);
}

// Track LLM usage
lynex.captureLLMUsage('gpt-4', 150, 300, 0.05);

// Track model responses
lynex.captureModelResponse(
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
import { Lynex } from '@lynex/sdk';

const client = lynex.init({
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
