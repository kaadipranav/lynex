export { WatchLLM } from './client';
export * from './types';

import { WatchLLM } from './client';
import type { WatchLLMConfig } from './types';

// Convenience exports for functional API
export function init(config: WatchLLMConfig) {
  return WatchLLM.init(config);
}

export function captureEvent(type: string, body: Record<string, any>, context?: Record<string, any>) {
  WatchLLM.getInstance().captureEvent(type, body, context);
}

export function captureLog(message: string, level: 'debug' | 'info' | 'warn' | 'error' = 'info', context?: Record<string, any>) {
  WatchLLM.getInstance().captureLog(message, level, context);
}

export function captureError(error: Error, context?: Record<string, any>) {
  WatchLLM.getInstance().captureError(error, context);
}

export function captureLLMUsage(model: string, inputTokens: number, outputTokens: number, cost?: number) {
  WatchLLM.getInstance().captureLLMUsage(model, inputTokens, outputTokens, cost);
}

export function captureModelResponse(
  model: string,
  latencyMs: number,
  success: boolean,
  usage?: { inputTokens: number; outputTokens: number },
  prompt?: string,
  response?: string
) {
  WatchLLM.getInstance().captureModelResponse(model, latencyMs, success, usage, prompt, response);
}

export function flush() {
  return WatchLLM.getInstance().flush();
}
