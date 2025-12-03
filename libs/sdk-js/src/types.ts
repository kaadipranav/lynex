export interface SentryAIConfig {
  apiKey: string;
  projectId: string;
  host?: string;
  batchSize?: number;
  flushInterval?: number;
  debug?: boolean;
}

export interface EventBody {
  [key: string]: any;
}

export interface SentryAIEvent {
  eventId: string;
  projectId: string;
  type: string;
  timestamp: string;
  sdk: {
    name: string;
    version: string;
  };
  body: EventBody;
  context?: Record<string, any>;
}

export interface LogBody {
  message: string;
  level: 'debug' | 'info' | 'warn' | 'error';
}

export interface ErrorBody {
  type: string;
  message: string;
  stacktrace?: string;
}

export interface TokenUsageBody {
  model: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  cost?: number;
}

export interface ModelResponseBody {
  model: string;
  prompt?: string;
  response?: string;
  latencyMs: number;
  success: boolean;
  usage?: {
    inputTokens: number;
    outputTokens: number;
    totalTokens: number;
  };
}
