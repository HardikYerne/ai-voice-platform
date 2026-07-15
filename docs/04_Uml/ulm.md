# UML Diagrams

## 1. Purpose

This document specifies the five UML views for the AI Voice Platform: Use Case,
Class, Activity, Sequence, and Deployment. Each section includes a rendered diagram
(Mermaid, so it previews directly on GitHub/GitLab) plus the structured spec you can
use to recreate/refine the same diagram in draw.io.

These trace back to the requirements in `docs/02_SRS/` and the design in
`docs/03_HLD/` and `docs/04_LLD/`.

---

## 2. Use Case Diagram

**Actors:**

| Actor | Description |
|---|---|
| Customer | Person calling in or being called |
| Business Admin | Configures the agent (knowledge base, tools, workflows) |
| Support/Ops Staff | Reviews transcripts, analytics; receives human handoffs |
| Telephony Provider | External system (not a human actor, but a system actor) |

**Use cases:**

- Call the business (Customer)
- Verify identity (Customer, System)
- Ask a question / get an answer (Customer)
- Book an appointment (Customer)
- Request a human agent (Customer)
- Receive an outbound call (Customer)
- Configure knowledge base (Business Admin)
- Configure tools/integrations (Business Admin)
- Review call transcript (Support/Ops Staff)
- Review analytics dashboard (Support/Ops Staff)
- Receive call transfer (Support/Ops Staff)

```mermaid
flowchart LR
    Customer((Customer))
    Admin((Business Admin))
    Ops((Support/Ops Staff))

    subgraph System["AI Voice Platform"]
        UC1["Call the business"]
        UC2["Verify identity"]
        UC3["Ask a question"]
        UC4["Book an appointment"]
        UC5["Request human agent"]
        UC6["Receive outbound call"]
        UC7["Configure knowledge base"]
        UC8["Configure tools/integrations"]
        UC9["Review transcript"]
        UC10["Review analytics dashboard"]
        UC11["Receive call transfer"]
    end

    Customer --> UC1
    Customer --> UC2
    Customer --> UC3
    Customer --> UC4
    Customer --> UC5
    Customer --> UC6
    Admin --> UC7
    Admin --> UC8
    Ops --> UC9
    Ops --> UC10
    Ops --> UC11
    UC5 -.include.-> UC11
    UC4 -.include.-> UC2
```

*In draw.io:* use the UML → Use Case shape set; actors as stick figures on the
left/right, use cases as ellipses inside a system boundary rectangle, `<<include>>`
relationships as dashed arrows.

---

## 3. Class Diagram

Core domain classes, matching the schemas defined in `docs/04_LLD/low_level_design.md`.

```mermaid
classDiagram
    class CallSession {
        +str call_id
        +str direction
        +str from_number
        +str to_number
        +str status
        +datetime started_at
        +datetime ended_at
        +str recording_url
    }

    class ConversationState {
        +str call_id
        +list~Turn~ turns
        +str detected_language
        +dict session_variables
        +append_turn(turn)
        +get_context(max_turns)
    }

    class Turn {
        +str role
        +str text
        +datetime timestamp
        +str language
    }

    class AgentState {
        +str call_id
        +ConversationState conversation
        +list scratchpad
        +str final_response
    }

    class ToolCall {
        +str tool_name
        +dict arguments
    }

    class ToolResult {
        +str tool_name
        +bool success
        +dict data
        +str error
    }

    class RetrievedChunk {
        +str text
        +str source_doc_id
        +float score
    }

    class LongTermMemory {
        +str customer_id
        +dict known_facts
        +datetime last_updated
    }

    class SessionMemory {
        +str call_id
        +dict working_facts
    }

    class CallAnalytics {
        +str call_id
        +list~Turn~ transcript
        +str summary
        +str sentiment
        +bool resolved
        +bool handed_off_to_human
        +list tools_used
        +int duration_seconds
    }

    CallSession "1" --> "1" ConversationState : has
    ConversationState "1" --> "*" Turn : contains
    AgentState "1" --> "1" ConversationState : wraps
    AgentState "1" --> "*" ToolCall : issues
    ToolCall "1" --> "1" ToolResult : produces
    AgentState "1" --> "*" RetrievedChunk : uses
    CallSession "1" --> "1" SessionMemory : has
    CallSession "1" --> "1" CallAnalytics : produces
    SessionMemory "*" --> "1" LongTermMemory : promotes facts to
```

*In draw.io:* UML → Class shape; three-compartment boxes (name / attributes /
methods), solid line + open diamond for composition (`CallSession` → `ConversationState`),
plain solid arrows for association/dependency as shown above.

---

## 4. Activity Diagram

Activity flow for handling a single inbound call turn, including decision points.

```mermaid
flowchart TD
    Start(["Call received"]) --> Answer["Answer call"]
    Answer --> Listen["Listen for caller speech"]
    Listen --> Transcribe["Transcribe (STT)"]
    Transcribe --> Intent{"Intent detected?"}
    Intent -- "no / unclear" --> Clarify["Ask clarifying question"]
    Clarify --> Listen
    Intent -- "yes" --> NeedsInfo{"Needs knowledge\nor action?"}
    NeedsInfo -- "knowledge" --> RAGLookup["Query knowledge base (RAG)"]
    NeedsInfo -- "action" --> ToolCall["Call tool (CRM/Calendar/etc.)"]
    NeedsInfo -- "neither" --> Draft["Draft response"]
    RAGLookup --> Draft
    ToolCall --> ToolOk{"Tool succeeded?"}
    ToolOk -- "yes" --> Draft
    ToolOk -- "no" --> Retry{"Retry attempted?"}
    Retry -- "no" --> ToolCall
    Retry -- "yes" --> Handoff["Offer human handoff"]
    Draft --> Speak["Synthesize and speak response (TTS)"]
    Speak --> More{"Call continues?"}
    More -- "yes" --> Listen
    More -- "no" --> End(["Call ends → generate summary"])
    Handoff --> End
```

*In draw.io:* UML → Activity shape set; rounded rectangles for actions, diamonds for
decisions, filled circle for start, circle-with-ring for end.

---

## 5. Sequence Diagram

A single conversational turn, end to end (matches `docs/04_LLD/` §2, expanded with
RAG/Tools detail).

```mermaid
sequenceDiagram
    actor Customer
    participant TP as Telephony Provider
    participant BE as Backend (FastAPI)
    participant STT as Speech (STT)
    participant AG as Agent (LangGraph)
    participant RAG as RAG
    participant TL as Tools
    participant LLM as LLM
    participant TTS as Speech (TTS)

    Customer->>TP: Speaks
    TP->>BE: Stream audio (WebSocket)
    BE->>STT: Audio chunk
    STT-->>BE: Transcript
    BE->>AG: Transcript + conversation context
    AG->>RAG: Query knowledge base (if needed)
    RAG-->>AG: Retrieved chunks
    AG->>TL: Execute tool call (if needed)
    TL-->>AG: Tool result
    AG->>LLM: Prompt (context + retrieved docs + tool results)
    LLM-->>AG: Response text
    AG-->>BE: Final response
    BE->>TTS: Text to synthesize
    TTS-->>BE: Audio stream
    BE->>TP: Stream audio
    TP->>Customer: Plays response
```

*In draw.io:* UML → Sequence shape set; lifelines for each participant, solid arrows
for synchronous calls, dashed arrows for returns — matches the flow above 1:1.

---

## 6. Deployment Diagram

Physical/infrastructure deployment of the services (traces to NFR-1, NFR-8, NFR-9).

```mermaid
flowchart TB
    subgraph Edge["Edge / Ingress"]
        LB["Load Balancer / Reverse Proxy"]
    end

    subgraph K8s["Container Orchestration (Docker / Kubernetes)"]
        subgraph TelNode["Telephony Service Pod(s)"]
            TelSvc["telephony-service"]
        end
        subgraph BENode["Backend Pod(s)"]
            APIGw["api-gateway (FastAPI)"]
        end
        subgraph AINode["AI Services Pod(s)"]
            SpeechSvc["speech-service"]
            AgentSvc["agent-service"]
            LLMSvc["llm-service"]
            RagSvc["rag-service"]
            ToolsSvc["tools-service"]
        end
        subgraph AnalyticsNode["Analytics Pod(s)"]
            AnalyticsSvc["analytics-service"]
        end
    end

    subgraph Data["Data Tier"]
        Redis[("Redis\n(session state)")]
        Postgres[("PostgreSQL\n(persistent data)")]
        VectorDB[("Vector DB\n(RAG index)")]
    end

    subgraph External["External Systems"]
        TwilioExt["Telephony Provider API"]
        LLMExt["LLM Provider API"]
        CRMExt["CRM / Calendar / Email APIs"]
    end

    LB --> TelSvc
    LB --> APIGw
    TelSvc <--> TwilioExt
    APIGw <--> Redis
    APIGw <--> Postgres
    APIGw --> AgentSvc
    AgentSvc --> LLMSvc
    AgentSvc --> RagSvc
    AgentSvc --> ToolsSvc
    LLMSvc <--> LLMExt
    RagSvc <--> VectorDB
    ToolsSvc <--> CRMExt
    APIGw --> AnalyticsSvc
    AnalyticsSvc --> Postgres
```

*In draw.io:* UML → Deployment shape set; 3D boxes ("nodes") for each pod/host,
cylinders for data stores, dashed arrows for external API dependencies.

---

## 7. Diagram-to-Requirement Traceability

| Diagram | Primarily validates |
|---|---|
| Use Case | FR-1–FR-2, FR-4–FR-5, FR-12–FR-15, FR-20 |
| Class | FR-8, FR-9, FR-11, FR-17–FR-21 |
| Activity | FR-4, FR-10–FR-11, FR-15 |
| Sequence | FR-3, FR-6–FR-11 |
| Deployment | NFR-1, NFR-2, NFR-8, NFR-9 |

---

## 8. Next Step

If you want native `.drawio` files (XML) to open directly in draw.io instead of
recreating these from the specs above, let me know and I can generate them per
diagram.