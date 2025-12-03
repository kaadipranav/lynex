import type { SentryAIConfig, SentryAIEvent, EventBody, TokenUsageBody } from './types';

const SDK_NAME = 'sentryai-js';
const SDK_VERSION = '0.1.0';

function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export class SentryAI {
  private static instance: SentryAI | null = null;
  
  private config: Required<SentryAIConfig>;
  private queue: SentryAIEvent[] = [];
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private isFlushing = false;

  constructor(config: SentryAIConfig) {
    this.config = {
      apiKey: config.apiKey,
      projectId: config.projectId,
      host: config.host?.replace(/\/$/, '') || 'http://localhost:8000',
      batchSize: config.batchSize || 10,
      flushInterval: config.flushInterval || 5000,
      debug: config.debug || false,
    };

    this.startFlushTimer();
    this.setupShutdownHandlers();
    SentryAI.instance = this;
  }

  static init(config: SentryAIConfig): SentryAI {
    if (SentryAI.instance) {
      console.warn('SentryAI already initialized');
      return SentryAI.instance;
    }
    return new SentryAI(config);
  }

  static getInstance(): SentryAI {
    if (!SentryAI.instance) {
      throw new Error('SentryAI not initialized. Call SentryAI.init() first.');
    }
    return SentryAI.instance;
  }

  private log(...args: any[]) {
    if (this.config.debug) {
      console.log('[SentryAI]', ...args);
    }
  }

  private startFlushTimer() {
    if (this.flushTimer) return;
    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  }

  private setupShutdownHandlers() {
    // Browser
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.flush(true));
      window.addEventListener('pagehide', () => this.flush(true));
    }
    
    // Node.js
    if (typeof process !== 'undefined') {
      process.on('beforeExit', () => this.flush(true));
      process.on('SIGTERM', () => {
        this.flush(true);
        process.exit(0);
      });
      process.on('SIGINT', () => {
        this.flush(true);
        process.exit(0);
      });
    }
  }

  captureEvent(type: string, body: EventBody, context?: Record<string, any>) {
    const event: SentryAIEvent = {
      eventId: generateUUID(),
      projectId: this.config.projectId,
      type,
      timestamp: new Date().toISOString(),
      sdk: {
        name: SDK_NAME,
        version: SDK_VERSION,
      },
      body,
      context,
    };

    this.queue.push(event);
    this.log('Event queued:', type, event.eventId);

    if (this.queue.length >= this.config.batchSize) {
      this.flush();
    }
  }

  captureLog(message: string, level: 'debug' | 'info' | 'warn' | 'error' = 'info', context?: Record<string, any>) {
    this.captureEvent('log', { message, level }, context);
  }

  captureError(error: Error, context?: Record<string, any>) {
    this.captureEvent('error', {
      type: error.name,
      message: error.message,
      stacktrace: error.stack,
    }, context);
  }

  captureLLMUsage(model: string, inputTokens: number, outputTokens: number, cost?: number) {
    const body: TokenUsageBody = {
      model,
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
      cost,
    };
    this.captureEvent('token_usage', body);
  }

  captureModelResponse(
    model: string,
    latencyMs: number,
    success: boolean,
    usage?: { inputTokens: number; outputTokens: number },
    prompt?: string,
    response?: string
  ) {
    this.captureEvent('model_response', {
      model,
      latencyMs,
      success,
      prompt,
      response,
      usage: usage ? { ...usage, totalTokens: usage.inputTokens + usage.outputTokens } : undefined,
    });
  }

  async flush(sync = false): Promise<void> {
    if (this.isFlushing || this.queue.length === 0) return;

    this.isFlushing = true;
    const events = this.queue.splice(0, this.config.batchSize);

    try {
      const url = `${this.config.host}/api/v1/events/batch`;
      
      const fetchFn = typeof fetch !== 'undefined' ? fetch : require('node-fetch');
      
      if (sync && typeof navigator !== 'undefined' && navigator.sendBeacon) {
        // Use sendBeacon for sync flush in browser
        navigator.sendBeacon(
          url,
          new Blob([JSON.stringify({ events })], { type: 'application/json' })
        );
        this.log('Flushed via sendBeacon:', events.length, 'events');
      } else {
        const response = await fetchFn(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': this.config.apiKey,
          },
          body: JSON.stringify({ events }),
        });

        if (!response.ok) {
          console.error('[SentryAI] Flush failed:', response.status);
          // Re-queue events on failure
          this.queue.unshift(...events);
        } else {
          this.log('Flushed:', events.length, 'events');
        }
      }
    } catch (error) {
      console.error('[SentryAI] Flush error:', error);
      // Re-queue events on failure
      this.queue.unshift(...events);
    } finally {
      this.isFlushing = false;
    }
  }

  shutdown() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
    this.flush(true);
  }
}
