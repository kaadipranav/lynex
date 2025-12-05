# Lynex - AI Observability Platform

> Enterprise-grade AI monitoring and observability for production LLM applications

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 16+](https://img.shields.io/badge/node.js-16+-green.svg)](https://nodejs.org/)

Lynex is a comprehensive AI observability platform that provides real-time monitoring, tracing, and analytics for LLM applications. Built for enterprises that need production-ready AI infrastructure.

## 🚀 Features

- **Real-time Event Ingestion**: Capture LLM interactions, errors, and performance metrics
- **Advanced Analytics**: ClickHouse-powered analytics with sub-second query performance
- **Prompt Versioning & Diffing**: Track prompt changes and their impact on performance
- **Enterprise Security**: RBAC, audit logs, and compliance features
- **Multi-tenant Billing**: Usage-based billing with Stripe integration
- **Cold Storage**: Automatic archival to S3 for cost optimization
- **Alerting & Notifications**: Configurable alerts via Slack, email, and webhooks
- **SDKs**: Easy integration with Python and JavaScript/TypeScript applications

## 📦 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose (for full stack)
- MongoDB, Redis, ClickHouse (or use Docker)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/lynex.git
   cd lynex
   ```

2. **Install Python SDK**
   ```bash
   pip install watchllm
   ```

3. **Install JavaScript SDK**
   ```bash
   npm install @watchllm/sdk
   ```

### Basic Usage

#### Python
```python
from watchllm import WatchLLM

# Initialize client
client = WatchLLM(api_key="your-api-key")

# Track LLM interactions
with client.trace("chat_completion") as trace:
    trace.log_input({"messages": [{"role": "user", "content": "Hello"}]})
    # Your LLM call here
    response = {"content": "Hi there!"}
    trace.log_output(response)
    trace.log_usage(tokens=150, cost=0.002)
```

#### JavaScript/TypeScript
```javascript
import { WatchLLM } from '@watchllm/sdk';

const client = new WatchLLM({ apiKey: 'your-api-key' });

async function chatCompletion() {
  const trace = client.trace('chat_completion');
  trace.logInput({ messages: [{ role: 'user', content: 'Hello' }] });

  // Your LLM call
  const response = { content: 'Hi there!' };
  trace.logOutput(response);
  trace.logUsage({ tokens: 150, cost: 0.002 });

  await trace.end();
}
```

## 🏗️ Architecture

Lynex consists of multiple microservices:

- **Ingest API**: High-throughput event ingestion with Redis queuing
- **Processor**: Event processing and ClickHouse storage
- **UI Backend**: REST API for the web dashboard
- **Billing Service**: Usage tracking and invoicing
- **Web Dashboard**: React-based monitoring interface

## 🐳 Local Development

1. **Start infrastructure**
   ```bash
   docker-compose up -d
   ```

2. **Install dependencies**
   ```bash
   # Install all service dependencies
   for service in services/*/; do cd $service && pip install -r requirements.txt && cd ../..; done
   ```

3. **Run services**
   ```bash
   # Ingest API
   python run_ingest.py

   # Processor
   python run_processor.py

   # UI Backend
   python run_ui_backend.py
   ```

4. **Start web dashboard**
   ```bash
   cd web
   npm install
   npm run dev
   ```

## 📊 Monitoring & Metrics

Lynex exposes Prometheus metrics on all services:

- Request latency and throughput
- Error rates and types
- Queue depths and processing times
- Storage metrics and costs

## 🔒 Security

- JWT-based authentication
- Role-based access control (RBAC)
- API key management
- Audit logging
- Data encryption at rest and in transit

## 📈 Enterprise Features

- **Multi-tenancy**: Isolated data and billing per organization
- **SSO Integration**: SAML/OAuth support
- **Custom Dashboards**: Build custom monitoring views
- **API Rate Limiting**: Configurable rate limits per endpoint
- **Data Retention**: Configurable retention policies
- **Compliance**: SOC 2, GDPR, HIPAA ready

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🆘 Support

- Documentation: [docs.lynex.ai](https://docs.lynex.ai)
- Issues: [GitHub Issues](https://github.com/your-org/lynex/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/lynex/discussions)

---

**Lynex** - Making AI observable, reliable, and cost-effective.</content>
<parameter name="filePath">d:\Lynex\README.md
