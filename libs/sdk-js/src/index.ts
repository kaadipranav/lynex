export { Lynex } from './client';
export * from './types';

import { Lynex } from './client';
import type { LynexConfig } from './types';

// Convenience exports for functional API
export function init(config: LynexConfig) {
  return Lynex.init(config);
}

export function captureEvent(type: string, body: Record<string, any>, context?: Record<string, any>) {
  Lynex.getInstance().captureEvent(type, body, context);
}

export function captureLog(message: string, level: 'debug' | 'info' | 'warn' | 'error' = 'info', context?: Record<string, any>) {
  Lynex.getInstance().captureLog(message, level, context);
}

export function captureError(error: Error, context?: Record<string, any>) {
  Lynex.getInstance().captureError(error, context);
}

export function captureLLMUsage(model: string, inputTokens: number, outputTokens: number, cost?: number) {
  Lynex.getInstance().captureLLMUsage(model, inputTokens, outputTokens, cost);
}

export function captureModelResponse(
  model: string,
  latencyMs: number,
  success: boolean,
  usage?: { inputTokens: number; outputTokens: number },
  prompt?: string,
  response?: string
) {
  Lynex.getInstance().captureModelResponse(model, latencyMs, success, usage, prompt, response);
}

export function flush() {
  return Lynex.getInstance().flush();
}
