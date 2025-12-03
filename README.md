<div align="center">

# •   S E N T R Y   F O R   A I   •

### **The last observability platform you'll ever need for AI**

*Every token traced • Every dollar accounted • Every hallucination caught*

[![Status](https://img.shields.io/badge/STATUS-PRIVATE_BETA-00ff00?style=for-the-badge)](https://sentryai.dev)
[![Shipping](https://img.shields.io/badge/SOLO-SHIPPING_LIKE_A_TEAM_OF_10-ff0066?style=for-the-badge)](https://twitter.com/kaadz_zz)
[![Dogfooding](https://img.shields.io/badge/DOGFOODING-15K+_REQ/DAY-00ffff?style=for-the-badge)](https://sentryai.dev)

## Sentry for AI — AI Observability Platform

```ascii
  ███████╗███████╗███╗   ██╗████████╗██████╗ ██╗   ██╗
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██╔══██╗██║   ██║
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██████╔╝╚██╗ ██╔╝
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██╔══██╗  ╚██╔╝ 
  ███████║███████╗██║ ╚████║   ██║   ██║  ██║  ╚██║  
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   

                S E N T R Y   F O R   A I

   Real-time observability for production LLMs, agents, RAG pipelines, and AI workflows.
```

[![FastAPI](https://img.shields.io/badge/FastAPI-LLM_Ingest_API-05998a?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-black?style=flat&logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-blue?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Redis Streams](https://img.shields.io/badge/Redis_Streams-Ingest_Buffer-red?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-Hot_Analytics_Store-ffcc00?style=flat&logo=clickhouse&logoColor=000)](https://clickhouse.com/)
[![Vite](https://img.shields.io/badge/Vite-5-8A2BE2?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind](https://img.shields.io/badge/Tailwind-3.3-38bdf8?style=flat&logo=tailwindcss)](https://tailwindcss.com/)
[![TanStack Query](https://img.shields.io/badge/TanStack_Query-5-fe4164?style=flat&logo=react-query&logoColor=white)](https://tanstack.com/query)
[![Mermaid](https://img.shields.io/badge/Diagrams-Mermaid-00b894?style=flat)](https://mermaid.js.org/)

</div>

---

## 🎯 What Beta Users Are Doing With It

<table>
<tr>
<td width="50%">

### 💸 Catching Cost Explosions
**Before hitting the bill**

> *"Caught a $47k/month cost explosion before it hit production. The alert fired at step 38 of a recursive agent loop. Saved our runway."*
> 
> — AI Startup Founder, 12-person team

</td>
<td width="50%">

### 🔍 Debugging Agent Chaos  
**47-step loops, visualized**

> *"Finally can see WHY my agent is calling the same tool 47 times. The step graph showed the loop at step 38. Fixed in 10 minutes."*
> 
> — Solo dev building AI SaaS

</td>
</tr>
<tr>
<td>

### 🛡️ Blocking PII Leaks
**Before compliance audit**

> *"Auto-detected PII in 3 prompts during beta testing. Blocked them before production. Compliance team is happy."*
> 
> — Healthcare AI Product Manager

</td>
<td>

### 📊 Proving ROI to Investors
**RAG actually works (with receipts)**

> *"Showed investors our RAG retrieval accuracy went from 40% to 87%. Got the bridge round. SentryAI had the receipts."*
> 
> — B2B AI Platform, Series A

</td>
</tr>
</table>

---

## ⚡ Features (Live or <14 Days Out)

| Feature | Status | Notes |
|---------|--------|-------|
| **Full prompt/response visibility** | 🟢 Live | Click → expand → copy |
| **Token & $ cost per call** | 🟢 Live | OpenAI, Anthropic, Groq, etc. |
| **Agent step graph visualizer** | 🟡 7 days | Loops, branches, tool calls |
| **PII + injection auto-detection** | 🟢 Live | Regex + LlamaGuard 3 |
| **Real-time dashboard + charts** | 🟢 Live | Tailwind + Recharts glory |
| **SDKs (Python + JS/TS)** | 🟢 Live | `pip install sentryai` • `npm i sentryai` |
| **Alerts → Slack/Discord/email** | 🟢 Live | Error rate, cost spikes, jailbreaks |
| **Stripe billing** | 🟢 Live | Free → Pro → pay-as-you-go |

---

## 🚀 Get Started in 60 Seconds

### Python
```python
pip install sentryai
```

```python
import sentryai
from openai import OpenAI

# One line init
sentryai.init(api_key="sk_live_xxx")

# Wrap your client (auto-instruments everything)
client = sentryai.wrap(OpenAI())

# That's it. Every call is now traced.
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# View in dashboard → https://app.sentryai.dev
```

### JavaScript/TypeScript
```bash
npm install sentryai
```

```typescript
import { SentryAI } from 'sentryai';
import Anthropic from '@anthropic-ai/sdk';

// One line init
SentryAI.init({ apiKey: 'sk_live_xxx' });

// Wrap your client
const client = SentryAI.wrap(new Anthropic());

// Every call traced automatically
const response = await client.messages.create({
    model: 'claude-sonnet-4',
    messages: [{ role: 'user', content: 'Hello!' }]
});
```

**Zero config. Zero refactoring. Just wrap and ship.**

---

## 📦 Built to Scale From Day 1

```
10k+ events/sec    → FastAPI + Redis Streams
Billions of rows   → ClickHouse (sub-10ms queries)  
Zero-downtime      → Separate ingest + processor
```

**Roadmap (no bullshit dates)**

```
→ Jan 2026 = Private beta (DM @kaadz_zz on my latest tweet)
→ Feb 2026 = Public launch + waitlist explodes  
→ Q2 2026 = $1M ARR or I delete the repo
```

---

## 🎪 One Founder. One Repo. About to 10x the AI observability game.

**Built in public.**

- Started: December 2024
- Shipped MVP: 3 weeks
- First paying customer: Week 4
- First $1K MRR: Week 8 (or I quit)

**The Tech Stack** (because you're gonna ask):

```
Frontend:  React + TypeScript + Tailwind + Recharts
Backend:   FastAPI + Python 3.11
Queue:     Redis Streams (Upstash)
Database:  ClickHouse (TimeSeries OLAP god-tier)
Hosting:   DigitalOcean + Vercel
Auth:      Appwrite (self-hosted)
Billing:   Stripe + usage metering
Observability: Sentry (ironic) + Prometheus
```

**Why solo?**
- Ship 10x faster without meetings
- AI pair programming (Claude Sonnet 4.5)
- 100% ownership until Series A
- Prove it works before hiring

---

## 💀 Competitors (and why they're sleeping)

| Tool | What They Do | What They Miss |
|------|--------------|----------------|
| **LangSmith** | Good observability | $$$, slow, complex setup |
| **Helicone** | Simple proxy | Limited features, no agent debugging |
| **Datadog** | Added AI support | Not AI-native, expensive AF |
| **Weights & Biases** | ML training focus | Not for production monitoring |
| **Arize AI** | ML observability | Academic, not dev-first |

**SentryAI:** Built for devs who ship AI features daily. Fast, cheap, powerful.

---

## 📊 Pricing (Beta Access)

| Tier | Price | Events/Month | Features |
|------|-------|--------------|----------|
| **Free** | $0 | 50K | Basic dashboard, 7-day retention |
| **Hobby** | $9 | 500K | Alerts, Slack integration, 30-day retention |
| **Pro** | $49 | 5M | Team seats, RBAC, 90-day retention |
| **Scale** | $199 | 20M | SSO, SLA, 1-year retention |
| **Enterprise** | Custom | Unlimited | On-prem, contracts, white-glove |

**All beta users get Pro for 6 months free.** DM for access.

---

## 🔗 Links

- **Website:** [sentryai.dev](https://sentryai.dev)
- **Docs:** [docs.sentryai.dev](https://docs.sentryai.dev)
- **Twitter:** [@kaadz_zz](https://twitter.com/kaadz_zz)
- **Discord:** [Join the AI debugging cult](https://discord.gg/sentryai)
- **Email:** kaadi@sentryai.dev

---

## ⭐ Star This Repo If You Want To See It Happen

```
git clone https://github.com/kaadipranav/sentryai
cd sentryai
make watch-me-build-in-public
```

**Building this solo. Every star = fuel.**

---

<div align="center">

### 🎯 The Mission

**Make AI debugging as easy as `console.log()`**

Stop guessing why your agents hallucinate.  
Stop bleeding money on bad prompts.  
Stop getting wrecked by PII leaks.

**Start shipping with confidence.**

---

*Built with rage, caffeine, and Claude Sonnet 4.5*

[![Twitter Follow](https://img.shields.io/twitter/follow/kaadz_zz?style=social)](https://twitter.com/kaadz_zz)
[![GitHub Stars](https://img.shields.io/github/stars/kaadipranav/sentryai?style=social)](https://github.com/kaadipranav/sentryai)

</div>
