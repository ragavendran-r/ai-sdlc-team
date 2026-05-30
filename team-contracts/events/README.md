# Event Definitions

This folder contains TypeScript definitions for all events emitted by agents in the system.

## Event Categories

### Status Events
Events emitted by agents to report progress, completion, or blocking issues.

- **`execution-status.ts`** - Task progress updates
  - Task started, in-progress, blocked, completed
  - Blocker details, estimated time to resolution

- **`requirement-updated.ts`** - Requirement status changes
  - Requirement clarified, scope changed
  - Impact analysis, dependent tasks affected

- **`design-ready.ts`** - Design specifications ready for implementation
  - Component specs finalized
  - Design system updates

- **`api-ready.ts`** - API specifications ready for frontend integration
  - Endpoints finalized, schemas approved
  - Error handling and authentication specs

### Coordination Events
Events that coordinate work between agents or signal readiness for handoff.

- **`handoff-ready.ts`** - General readiness for handoff
  - Sender agent, receiver agent, handoff type
  - Context reference, artifacts

- **`blocker-identified.ts`** - Work is blocked, needs intervention
  - Blocker description, blocking agent/task
  - Requested action, urgency level

- **`scope-change.ts`** - Scope has changed
  - What changed, impact, affected agents
  - Recommended actions

### Decision Events
Events that record important team decisions.

- **`priority-decision.ts`** - Priority determination or change
  - Feature/task, new priority, reasoning
  - Impact on timeline and dependencies

- **`technical-decision.ts`** - Technical architecture decision
  - Decision summary, alternatives considered
  - Rationale, impact on other agents

- **`requirement-clarification.ts`** - Requirement has been clarified
  - Original requirement, clarification, source
  - Impact on estimates and design

## Event Structure

Each event file follows this pattern:

```typescript
// events/execution-status.ts
export type ExecutionStatus = 'started' | 'in-progress' | 'blocked' | 'completed' | 'failed';

export interface ExecutionStatusEvent {
  id: string;                    // Unique event ID
  timestamp: Date;
  task_id: string;              // Reference to task
  agent: string;                // Emitting agent
  status: ExecutionStatus;
  progress_percentage?: number;
  blocker?: BlockerDetail;
  completed_at?: Date;
  context_id?: string;          // Reference to shared context
  metadata?: Record<string, any>;
}

export interface BlockerDetail {
  description: string;
  blocking_agent?: string;
  blocking_on?: string;
  requested_action?: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
}
```

## Event Registry

The `index.ts` file exports all event types and provides a registry:

```typescript
// events/index.ts
export * from './execution-status';
export * from './requirement-updated';
export * from './design-ready';
// ... other events

export type TeamEvent = 
  | ExecutionStatusEvent
  | RequirementUpdatedEvent
  | DesignReadyEvent
  // ... other event types
```

## Publishing Events

Agents publish events to a central event bus. Example:

```typescript
// In agent code
const event: ExecutionStatusEvent = {
  id: uuid(),
  timestamp: new Date(),
  task_id: task.id,
  agent: 'frontend-agent',
  status: 'completed',
  completed_at: new Date(),
  context_id: contextId
};

await eventBus.publish(event);
```

## Subscribing to Events

Agents subscribe to events they care about:

```typescript
// In agent code
eventBus.subscribe('execution-status', (event: ExecutionStatusEvent) => {
  if (event.agent === 'backend-agent' && event.status === 'blocked') {
    // Take action on backend blockers
  }
});
```

## Adding New Events

1. Create a new event file: `{event-name}.ts`
2. Define the interface with all required and optional fields
3. Export the type
4. Add to event registry in `index.ts`
5. Document in this README
6. Update agents that should subscribe to this event

## Event Sourcing

Critical events are logged for:
- Audit trail (who made decisions, when)
- Timeline reconstruction (understanding how we got here)
- Replay (reconstructing state if needed)

Key events to source:
- Requirement changes
- Priority decisions
- Technical decisions
- Scope changes
- Major blocker/resolution cycles
