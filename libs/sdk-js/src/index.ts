export { SentryAI } from './client';
export * from './types';

import { SentryAI } from './client';
import type { SentryAIConfig } from './types';

// Convenience exports for functional API
export function init(config: SentryAIConfig) {
  return SentryAI.init(config);
}

export function captureEvent(type: string, body: Record<string, any>, context?: Record<string, any>) {
  SentryAI.getInstance().captureEvent(type, body, context);
}

export function captureLog(message: string, level: 'debug' | 'info' | 'warn' | 'error' = 'info', context?: Record<string, any>) {
  SentryAI.getInstance().captureLog(message, level, context);
}

export function captureError(error: Error, context?: Record<string, any>) {
  SentryAI.getInstance().captureError(error, context);
}

export function captureLLMUsage(model: string, inputTokens: number, outputTokens: number, cost?: number) {
  SentryAI.getInstance().captureLLMUsage(model, inputTokens, outputTokens, cost);
}

export function captureModelResponse(
  model: string,
  latencyMs: number,
  success: boolean,
  usage?: { inputTokens: number; outputTokens: number },
  prompt?: string,
  response?: string
) {
  SentryAI.getInstance().captureModelResponse(model, latencyMs, success, usage, prompt, response);
}

export function flush() {
  return SentryAI.getInstance().flush();
}
