# Mnemos - Memory Meets Intelligence

**Hackathon Date:** 9 February 2026

**Team Mnemos:** Sapna Chavan · Saurabh Chavan · Rohit Kosamkar

## Inspiration

Mnemos was inspired by small but repeated moments that all of us on the team experienced in our daily lives.

We would capture screenshots of something interesting, bookmark a job post or a research paper, or save a technical thread with the intention of coming back to it later. But work continued, meetings started, priorities shifted, and those intentions quietly faded. Deadlines passed, opportunities expired, and valuable information remained scattered across tools that were never designed to work together.

We realized the problem was not a lack of information, but the gap between **information consumption and meaningful action**. Existing tools are reactive, they store information, but they wait. They do not understand intent, urgency, or timing. We wanted a system that continues working even when our attention moves elsewhere.

That need led us to build **Mnemos**.

 

## What It Does

Mnemos is a desktop-based AI-powered second brain that captures information the moment it appears and continues working on it in the background.

With a single shortcut (Ctrl + Shift + L) or a widget, users can capture screenshots, voice notes, text snippets, and documents - all without breaking focus.

**Gemini 3** then understands the content, context, and intent behind each capture, classifies it across life domains using a three-layer universal classification framework, and extracts actionable items such as deadlines, follow-ups, or tasks.

### Beyond Storage

What makes Mnemos distinct is what happens after capture. While the user continues working, Mnemos proactively:

- Researches relevant resources, articles, and documentation on the user's behalf
- Creates Google Calendar events, Tasks, and reminders automatically
- Monitors time-sensitive information and notifies users before important moments are missed
- Drafts email responses for messages requiring replies

Users can later interact with their memory using **natural language**, retrieving information semantically rather than by keywords.



## High-Level Architecture

Mnemos follows a **modular, event-driven, multi-agent architecture** powered by Gemini 3. The system is composed of distinct layers that handle authentication, user interaction, understanding, orchestration, storage, and integrations.

![Mnemos High-Level Architecture](https://raw.githubusercontent.com/SapnaSChavan/gemini-hackathon-2026/2fb7b5b91be85720f0b493527bf229ae48f16de8/architecture/MnemosHighLevelArchitecture.png)

### Frontend and Desktop Layer

An Electron-based desktop application provides cross-platform support with native OS integrations. Users can instantly capture screenshots, audio, text, or documents through a keyboard shortcut or widget, with minimal workflow interruption.

### API Layer

FastAPI serves as the central backend gateway, handling REST APIs, WebSocket connections for real-time updates, and routing requests to Gemini 3-powered agents.

### Capture and Understanding Layer

Raw user input is converted into structured, meaningful information using Gemini 3's multimodal capabilities   performing OCR on screenshots, transcribing audio, and analyzing visual context.

### Event Bus

A centralized event bus enables asynchronous, priority-based processing. Once intent analysis completes, events are published for downstream agents to consume independently, supporting loose coupling and parallel execution.

### Multi-Agent System

Eight specialized Gemini 3-powered agents handle distinct cognitive functions across two processing tiers:

**Core Processing Tier**

| Agent | Function |
| -| -|
| **Perception Agent** | Performs OCR on screenshots, transcribes audio, and generates semantic descriptions of visual content to extract structured information from raw inputs. |
| **Classification Agent** | Analyzes content through a three-layer framework (life domain, context type, intent) and extracts 1 to 14 discrete actionable items from a single capture. |
| **Orchestration Agent** | Executes classified actions through fifteen specialized tools   creating calendar events, generating tasks with due dates, and populating domain-specific collections. |
| **Research Agent** | Activates selectively when content indicates research value. Searches for solutions, tutorials, and documentation using Gemini 3's Google Search grounding, and synthesizes findings with source citations. |
| **Proactive Agent** | Monitors captures continuously (2-minute intervals) for time-sensitive information and approaching deadlines, generating graduated notifications based on urgency. Checks scheduling conflicts and surfaces relevant context. |
| **Resource Finder Agent** | Autonomously determines when learning resources would accelerate user progress, then discovers, evaluates, and curates 3 to 5 high-quality materials with learning path recommendations. |
| **Email Intelligence Assistant** | Runs as a daily scheduled job analyzing the user's Gmail inbox from the previous 24 hours. Identifies emails requiring responses, generates professional draft replies matched to appropriate tone, and saves them directly to Gmail Drafts for user review. |

Agents communicate through a priority-based event bus with staggered invocation to prevent API rate limiting while maintaining responsiveness.

### Retrieval-Augmented Generation (RAG)

A RAG pipeline using text-embedding-004 converts captured content into vector representations. Vertex AI Search enables scalable semantic retrieval, allowing users to ask natural language questions about previously captured knowledge.

### Storage and Persistence

- **Google Cloud Storage**   Files, screenshots, and documents
- **Firestore**   Structured metadata, task state, and application configuration
- **Vertex AI Search**   Indexed semantic retrieval

### External Integrations

Secure OAuth2 integration with Google services enables automatic synchronization with Google Calendar, Tasks, Gmail, and Notes. Actions extracted by Gemini 3 are converted into calendar events, tasks, reminders, or drafted emails without manual effort.



## Physical Architecture

Mnemos is deployed entirely on Google Cloud Platform using secure, scalable, and service-oriented infrastructure. All components are hosted in the us-central1 region.

![Mnemos Physical Architecture](https://raw.githubusercontent.com/SapnaSChavan/gemini-hackathon-2026/2fb7b5b91be85720f0b493527bf229ae48f16de8/architecture/MnemosPhysicalArchitecture.png)

Key infrastructure decisions include:

- **Compute**: All backend services and agent runtimes run on Google Cloud Run as containerized, stateless workloads with automatic horizontal scaling.
- **AI Inference**: Gemini 3 is accessed through Vertex AI with Model Armor enforcing safety and compliance controls.
- **Identity and Access**: Google OAuth for user authentication; dedicated service accounts with least-privilege IAM roles for all backend services. No static secrets or embedded API keys.
- **Semantic Search**: Text embeddings via text-embedding-004, indexed through Vertex AI Search for low-latency, meaning-based retrieval.
- **Observability**: Google Cloud Logging, Monitoring, and Tracing for centralized operational visibility across all services.


## Three-Layer Universal Classification Framework

Mnemos classifies every capture through three layers to achieve structured, domain-agnostic understanding:

**Layer 1   Life Domains (12 categories):** Work and Career, Education and Learning, Money and Finance, Home and Daily Life, Health and Wellbeing, Family and Relationships, Travel and Movement, Shopping and Consumption, Entertainment and Leisure, Social and Community, Administration and Documents, Ideas and Thoughts.

**Layer 2   Context Types (19 formats):** Email, Chat Message, Document/PDF, Web Page, Application Screen, Form, Receipt/Invoice, Calendar Item, Social Media Post, Code/Terminal Output, Spreadsheet, Notification, Image, Audio Note, Video, Presentation, Task Item, Research Paper, Miscellaneous.

**Layer 3   Intent Categories (14 action types):** Act, Schedule, Pay, Buy, Remember, Learn, Track, Reference, Research, Compare, Follow Up, Wait, Archive, Ignore.


## Tech Stack

**Backend:** Python, FastAPI, Pydantic, Uvicorn, Celery, asyncio, Google Cloud SDK, Google Gen AI SDK

**Desktop Frontend:** Electron.js, Node.js, HTML5, CSS3, JavaScript, Electron IPC

**AI and Intelligence:** Gemini 3 via Vertex AI, text-embedding-004, Vertex AI Search, RAG pipeline

**Database and Storage:** Firestore (NoSQL), Google Cloud Storage

**Deployment:** Docker, Google Cloud Run, Google Secret Manager, IAM

**DevOps:** Google Cloud Logging and Monitoring, Git, GitHub, Pytest, Jest

**Security:** HTTPS/SSL, OAuth2, JWT, role-based access control


## Challenges We Ran Into

The biggest challenge was moving from a **reactive chatbot mindset to a proactive system**. Key challenges included:

- **Decision Intelligence**   Determining when Mnemos should act and when it should stay silent required careful reasoning and threshold tuning.
- **Multi-Action Extraction**   Extracting multiple discrete actions from a single capture, each with independent deadlines and execution requirements.
- **Multimodal Processing**   Handling unstructured screenshots reliably with high accuracy across diverse application contexts.
- **Performance Balance**   Balancing low-latency synchronous feedback with deep asynchronous background processing.
- **Context Preservation**   Maintaining user context across multiple life domains and timeframes without losing relevance.



## Accomplishments We Are Proud Of

- Built a fully functional **proactive system** with nine specialized AI agents, not just a chatbot.
- Designed a **multi-agent architecture** with tiered synchronous and asynchronous processing powered by Gemini 3.
- Enabled instant, **low-friction desktop capture** without interrupting user workflow.
- Implemented **semantic memory** with RAG-based natural language recall across all captured content.
- Developed an **Email Intelligence Assistant** that autonomously drafts professional responses from inbox analysis.
- Built a product **we personally rely on every day**.



## What We Learned

We learned that **intelligence alone is not enough**. Timing, context, and restraint are equally important.

Gemini 3's multimodal reasoning and long-context capabilities allowed us to move beyond simple retrieval into intelligent planning, contextual memory, and proactive assistance. The journey taught us that the best AI systems are those that **amplify human capability without demanding constant attention**.



## What Is Next for Mnemos

**Short-term Goals**
- Cross-device synchronization
- Deeper integrations with productivity tools (Slack, Notion, Linear)
- Improved personalized prioritization
- Native macOS desktop application

**Long-term Vision**
- Enhanced proactive intelligence with predictive insights
- Team collaboration features
- Enterprise-grade security and privacy controls
- Mobile application for seamless access anywhere

Our ultimate goal is for Mnemos to feel **less like software and more like an extension of human memory**.

---

Built for the Gemini Hackathon Google DeepMind
