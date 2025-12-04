# Lynex JavaScript/TypeScript SDK

Official JavaScript SDK for [Lynex](https://lynex.dev) - AI Observability Platform.

Monitor your AI/LLM applications with ease. Track model calls, token usage, errors, and performance metrics.

## Installation

```bash
npm install @lynex/sdk
# or
yarn add @lynex/sdk
# or
pnpm add @lynex/sdk
```

## Quick Start

```typescript
import { Lynex, init, captureLog, captureError, captureLLMUsage } from '@lynex/sdk';

// Initialize the SDK
init({
  apiKey: 'your-api-key',
  projectId: 'your-project-id',
  host: 'http://localhost:8001', // Optional, your Lynex API endpoint
  debug: true, // Optional, enables console logging
});

// Capture a log message
captureLog('User started chat session', 'info', { userId: 'user-123' });

// Capture LLM token usage
captureLLMUsage('gpt-4', 150, 500, 0.02);

// Capture errors
try {
  // Your AI code
} catch (error) {
  captureError(error as Error, { context: 'chat-completion' });
}
```

## API Reference

### Initialization

```typescript
import { init } from '@lynex/sdk';

init({
  apiKey: string;         // Required: Your Lynex API key
  projectId: string;      // Required: Your project ID
  host?: string;          // Optional: API host (default: http://localhost:8001)
  batchSize?: number;     // Optional: Events before auto-flush (default: 10)
  flushInterval?: number; // Optional: Auto-flush interval in ms (default: 5000)
  debug?: boolean;        // Optional: Enable debug logging (default: false)
});
```

### Capturing Events

#### Log Messages

```typescript
import { captureLog } from '@lynex/sdk';

captureLog('Application started');
captureLog('User logged in', 'info', { userId: 'user-123' });
captureLog('Rate limit approaching', 'warn', { remaining: 10 });
```

#### Errors

```typescript
import { captureError } from '@lynex/sdk';

try {
  await openai.chat.completions.create({ ... });
} catch (error) {
  captureError(error as Error, { model: 'gpt-4' });
}
```

#### LLM Token Usage

```typescript
import { captureLLMUsage } from '@lynex/sdk';

captureLLMUsage('gpt-4-turbo', 150, 500, 0.03);
```

#### Model Response

```typescript
import { captureModelResponse } from '@lynex/sdk';

captureModelResponse(
  'gpt-4',
  1250, // latency in ms
  true, // success
  { inputTokens: 150, outputTokens: 500 },
  'What is AI?',
  'AI is...'
);
```

### Class-based API

```typescript
import { Lynex } from '@lynex/sdk';

const client = Lynex.init({
  apiKey: 'your-api-key',
  projectId: 'your-project-id',
});

client.captureLog('Hello!');
client.captureLLMUsage('gpt-4', 100, 200);

// Get existing instance anywhere
const instance = Lynex.getInstance();
```

### Manual Flush

```typescript
import { flush } from '@lynex/sdk';

await flush();
```

## Features

- ✅ Non-blocking event queue
- ✅ Auto-batching (sends every 10 events or 5 seconds)
- ✅ Graceful shutdown with flush
- ✅ Works in Node.js and browsers
- ✅ Full TypeScript support
- ✅ Zero-config defaults

## TypeScript Support

```typescript
import type { LynexConfig, LynexEvent, EventBody } from '@lynex/sdk';
```

## License

MIT
