# EVENT_SCHEMA.md

This file defines the **unified event schema** for all ingestion into the Sentry‑for‑AI system. Every SDK (Python, JS, Go, Swift, Node, Rust) sends events using these structures. The schema is intentionally flexible for future extensibility while preserving strict typing for analytics.

---

# 1. OVERVIEW

All events follow this envelope:

```
EventEnvelope {
  eventId: string
  projectId: string
  type: EventType
  timestamp: ISODate
  sdk: {
    name: string
    version: string
  }
  context?: object
  body: EventBody
}
```

**EventType**:

* `log`
* `error`
* `span`
* `token_usage`
* `message`
* `eval_metric`
* `agent_action`
* `retrieval`
* `tool_call`
* `model_response`
* `custom`

---

# 2. EVENT TYPES

Below is the full list of event bodies.

---

## 2.1 LOG EVENT

```
LogEvent {
  level: "debug" | "info" | "warn" | "error"
  message: string
  metadata?: object
}
```

---

## 2.2 ERROR EVENT

```
ErrorEvent {
  message: string
  stack?: string
  fingerprint?: string[]
  metadata?: object
}
```

---

## 2.3 SPAN EVENT (TRACING)

Used to track model calls, tool usage, RAG steps, etc.

```
SpanEvent {
  spanId: string
  parentSpanId?: string
  name: string
  start: ISODate
  end?: ISODate
  attributes?: object
}
```

---

## 2.4 TOKEN USAGE EVENT

```
TokenUsageEvent {
  model: string
  inputTokens: number
  outputTokens: number
  costUSD?: number
}
```

---

## 2.5 MESSAGE EVENT (PROMPTS & RESPONSES)

```
MessageEvent {
  role: "user" | "system" | "assistant" | "tool"
  content: string
  metadata?: object
}
```

---

## 2.6 MODEL RESPONSE EVENT

Captures model output with reasoning traces.

```
ModelResponseEvent {
  model: string
  prompt: string
  response: string
  finishReason?: string
  latencyMs: number
  metadata?: object
}
```

---

## 2.7 AGENT ACTION EVENT

Tracks agent frameworks (AutoGen, ReAct, etc.).

```
AgentActionEvent {
  agentName?: string
  action: string
  input: string
  output?: string
  reasoning?: string
  metadata?: object
}
```

---

## 2.8 RETRIEVAL EVENT (RAG)

```
RetrievalEvent {
  query: string
  results: [
    {
      id: string
      score: number
      text: string
      metadata?: object
    }
  ]
  vectorDimensions?: number
}
```

---

## 2.9 TOOL CALL EVENT

```
ToolCallEvent {
  toolName: string
  arguments: object
  result?: object
  latencyMs?: number
  metadata?: object
}
```

---

## 2.10 EVAL METRIC EVENT

```
EvalMetricEvent {
  suiteId: string
  metric: string
  value: number
  metadata?: object
}
```

---

## 2.11 CUSTOM EVENT

Allows advanced teams to send extended data.

```
CustomEvent {
  name: string
  payload: object
}
```

---

# 3. EVENT RELATIONSHIPS

### Trace = collection of related spans + messages + model events.

* Each event may contain `traceId`, but spans form the backbone.

### A model call typically generates:

1. SpanEvent (start)
2. MessageEvent (prompt)
3. RetrievalEvents (optional)
4. ToolCallEvents (optional)
5. ModelResponseEvent
6. TokenUsageEvent
7. SpanEvent (end)

This unified structure allows:

* cost analysis
* debugging
* full reasoning visualization
* performance analytics

---

# 4. RESERVED FIELDS

Across all events, the platform auto-adds:

* `ip` (if server-side)
* `runtime` (node/python/go/swift)
* `awsRegion` / `gcpZone` / `vercelRegion` if detected
* `requestId` if available

---

# 5. FUTURE EXTENSIONS

Room left for:

* **GPU runtime events** (latency, VRAM)
* **diff model comparisons**
* **session-level analytics**
* **reasoning graph reconstruction**

This schema is designed to support a 100M+ valuation AI observability product.
