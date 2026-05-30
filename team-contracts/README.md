# Team Contracts - Inter-Agent Communication Layer

## Purpose

The team contracts define the **communication protocols, schemas, and shared state** that enable agents to collaborate reliably. This is the contract layer that ensures:

- **Schema Validation**: All handoffs between agents use validated contracts
- **Event-Driven Communication**: Agents emit and subscribe to well-defined events
- **Shared Context**: A central context store maintains team-wide state
- **Type Safety**: TypeScript/JSON schemas ensure consistency across agents

## Architecture

```
┌─────────────────────────────────────────────┐
│        Shared Context Store                 │
│  (Team state, decisions, dependencies)      │
└─────────────────────────────────────────────┘
         ↑                ↑                ↑
    ┌────────────┐  ┌──────────────┐  ┌────────────┐
    │  Schemas   │  │    Events    │  │ Contracts  │
    │ (Handoff   │  │  (Status,    │  │ (Msg       │
    │  Messages) │  │   Updates)   │  │  Templates)│
    └────────────┘  └──────────────┘  └────────────┘
```

## Folder Structure

```
team-contracts/
├── schemas/          # Handoff contract definitions (JSON Schema, TypeScript types)
├── events/           # Event type definitions and registry
├── context-store/    # Shared context schema and management
└── README.md
```

### Folders

**`schemas/`**
- Defines the structure of handoffs between agents
- Examples:
  - `po-to-em.schema.json` - Requirements and priorities handoff
  - `ux-to-frontend.schema.json` - Design specifications handoff
  - `backend-to-frontend.schema.json` - API contract handoff
- Each schema includes:
  - Input structure
  - Validation rules
  - Required fields
  - Examples

**`events/`**
- Defines event types emitted by agents
- Examples:
  - `execution-status.event.ts` - Task progress and blocking issues
  - `requirement-updated.event.ts` - Requirements changed
  - `design-ready.event.ts` - Design specifications are ready for implementation
- Event registry ensures agents subscribe to the right events

**`context-store/`**
- Defines the shape of shared team state
- Includes:
  - Current roadmap and priorities
  - In-flight requirements and specs
  - Task assignments and status
  - Technical constraints and decisions
  - Team context (team members, capacity, deadlines)

## Key Principles

1. **Schema-First**: All inter-agent communication is validated against schemas
2. **Immutable Contracts**: Once published, contracts stay stable for backward compatibility
3. **Semantic Versioning**: Breaking changes increment the contract version
4. **Event Sourcing**: Critical events are logged for audit and replay
5. **Context as Source of Truth**: Shared context store is the single source of truth for team state

## Usage

### For Agent Developers

1. **Sending a Handoff**: 
   - Load the appropriate schema from `schemas/`
   - Validate your output against the schema
   - Emit the handoff event
   - Update the shared context

2. **Receiving a Handoff**:
   - Subscribe to the appropriate event type from `events/`
   - Validate incoming data against the schema
   - Read context from `context-store/`
   - Update your local state

3. **Emitting Status**:
   - Use `events/execution-status.event.ts` to report progress
   - Update shared context with blockers or completed work

### For Integration Tests

- Load schemas to validate agent outputs
- Load event definitions to verify agent subscriptions
- Use context-store schema to validate shared state updates

## Examples

### PO → EM Handoff
```
Schema: schemas/po-to-em.schema.json
Event: events/requirement-ready.event.ts
Context Update: Update roadmap in context-store/team-context.ts
```

### UX → Frontend Handoff
```
Schema: schemas/ux-to-frontend.schema.json
Event: events/design-ready.event.ts
Context Update: Add design specs to context-store/active-specs.ts
```

### Backend → Frontend API Contract
```
Schema: schemas/backend-to-frontend.schema.json
Event: events/api-ready.event.ts
Context Update: Register endpoints in context-store/api-registry.ts
```

## Development Notes

- Add new handoff schemas to `schemas/` before implementing agents
- Define corresponding events in `events/` for status and completion
- Update `context-store/` schema when adding new shared state
- Version contracts carefully to avoid breaking existing agents
- Keep schemas simple and focused — one handoff per schema
