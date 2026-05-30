# Context Store - Shared Team State

## Purpose

The context store is the **single source of truth** for team-wide state. Instead of each agent maintaining its own view of reality, all agents read from and write to this shared context. This ensures:

- **Consistency**: All agents see the same current state
- **Traceability**: Changes to state are tracked and attributed
- **Non-blocking Collaboration**: Agents don't need to wait for synchronous handoffs; they can check context asynchronously
- **Easy Integration Testing**: Tests can set up shared context and verify agent behavior

## Store Structure

The context store contains several key collections:

### 1. **Team Context** (`team-context.ts`)
Team-wide information and metadata.

```typescript
interface TeamContext {
  team_name: string;
  current_sprint: SprintInfo;
  team_capacity: TeamCapacity;
  deadlines: DeadlineInfo[];
  constraints: TeamConstraint[];
  decisions: Decision[];        // Historic decisions
  last_updated: Date;
}
```

### 2. **Roadmap & Priorities** (`roadmap.ts`)
High-level roadmap and feature priorities.

```typescript
interface Roadmap {
  current_quarter: QuarterInfo;
  features: Feature[];           // All features in roadmap
  active_features: string[];     // Feature IDs currently in work
  priorities: FeaturePriority[]; // Priority ordering
  milestones: Milestone[];
  updated_by: string;           // Last agent to update
  last_updated: Date;
}

interface Feature {
  id: string;
  name: string;
  description: string;
  business_value: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  status: 'backlog' | 'active' | 'in-progress' | 'review' | 'done';
  owner_agent: string;          // Which agent owns this
}
```

### 3. **Active Requirements** (`active-requirements.ts`)
Current requirements in development.

```typescript
interface ActiveRequirements {
  requirements: Requirement[];
  by_id: Map<string, Requirement>;
  by_feature: Map<string, string[]>;  // Feature ID → Requirement IDs
  status_summary: RequirementStatusSummary;
}

interface Requirement {
  id: string;
  feature_id: string;
  title: string;
  description: string;
  acceptance_criteria: string[];
  priority: number;
  owner_agent: 'po-agent';
  status: 'draft' | 'ready' | 'in-progress' | 'complete';
  dependencies: string[];       // Other requirement IDs
  created_at: Date;
  last_updated: Date;
}
```

### 4. **Active Design Specs** (`active-specs.ts`)
Current design specifications.

```typescript
interface ActiveDesignSpecs {
  specs: DesignSpec[];
  by_id: Map<string, DesignSpec>;
  by_feature: Map<string, string[]>;
  status_summary: DesignStatusSummary;
}

interface DesignSpec {
  id: string;
  feature_id: string;
  requirement_id: string;
  title: string;
  component_specs: ComponentSpec[];
  design_system_updates: DesignTokenUpdate[];
  interactions: InteractionSpec[];
  owner_agent: 'ux-agent';
  status: 'draft' | 'review' | 'ready' | 'implemented';
  created_at: Date;
  last_updated: Date;
  approved_by?: string;
}
```

### 5. **API Registry** (`api-registry.ts`)
Backend API specifications and availability.

```typescript
interface APIRegistry {
  endpoints: APIEndpoint[];
  by_id: Map<string, APIEndpoint>;
  by_feature: Map<string, string[]>;
  status_summary: APIStatusSummary;
  version: string;
  last_updated: Date;
}

interface APIEndpoint {
  id: string;
  feature_id: string;
  method: string;
  path: string;
  request_schema: JSONSchema;
  response_schema: JSONSchema;
  error_responses: ErrorSpec[];
  auth_required: boolean;
  owner_agent: 'backend-agent';
  status: 'draft' | 'spec-ready' | 'implemented' | 'tested';
  created_at: Date;
  last_updated: Date;
}
```

### 6. **Task Assignment** (`task-assignment.ts`)
Current work assignments and task graph.

```typescript
interface TaskAssignment {
  tasks: Task[];
  by_id: Map<string, Task>;
  by_agent: Map<string, string[]>;
  by_status: Map<string, string[]>;
  dependency_graph: TaskGraph;
  updated_by: string;           // Last agent to update
  last_updated: Date;
}

interface Task {
  id: string;
  title: string;
  feature_id: string;
  description: string;
  assigned_to: string;          // Agent ID
  type: 'design' | 'frontend' | 'backend' | 'integration-test';
  status: 'assigned' | 'in-progress' | 'blocked' | 'review' | 'complete';
  acceptance_criteria: string[];
  blockers: TaskBlocker[];
  created_at: Date;
  updated_at: Date;
  estimated_hours?: number;
  actual_hours?: number;
}
```

### 7. **Active Blockers** (`active-blockers.ts`)
Current blocking issues.

```typescript
interface ActiveBlockers {
  blockers: Blocker[];
  by_id: Map<string, Blocker>;
  by_task: Map<string, string[]>;
  by_agent: Map<string, string[]>;
  summary: BlockerSummary;
}

interface Blocker {
  id: string;
  task_id: string;
  blocking_agent: string;
  blocking_on_agent?: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: Date;
  updated_at: Date;
  status: 'open' | 'in-resolution' | 'resolved';
  resolution_plan?: string;
}
```

### 8. **Technical Decisions** (`technical-decisions.ts`)
Architectural and technical decisions made by the team.

```typescript
interface TechnicalDecisions {
  decisions: TechDecision[];
  by_id: Map<string, TechDecision>;
  by_feature: Map<string, string[]>;
  affected_agents: Map<string, string[]>;
}

interface TechDecision {
  id: string;
  feature_id: string;
  title: string;
  decision_summary: string;
  alternatives_considered: Alternative[];
  chosen_approach: string;
  rationale: string;
  affected_agents: string[];
  made_by: string;
  made_at: Date;
  impact_on_timeline?: string;
  impact_on_architecture?: string;
}
```

## Usage Patterns

### Reading from Context

```typescript
// In agent code
const activeReqs = await contextStore.get('active-requirements');
const myTasks = activeReqs.requirements.filter(r => r.feature_id === currentFeatureId);

// Check for blockers
const blockers = await contextStore.get('active-blockers');
const myBlockers = blockers.blockers.filter(b => b.blocking_agent === myAgentId);
```

### Writing to Context

```typescript
// In agent code
const requirement: Requirement = {
  id: uuid(),
  feature_id: featureId,
  title: "User login form",
  description: "...",
  acceptance_criteria: [...],
  priority: 1,
  owner_agent: 'po-agent',
  status: 'ready',
  dependencies: [],
  created_at: new Date(),
  last_updated: new Date()
};

await contextStore.update('active-requirements', (reqs) => {
  reqs.requirements.push(requirement);
  reqs.by_id.set(requirement.id, requirement);
  return reqs;
});
```

## Consistency Guarantees

- **Write Isolation**: Only the owning agent should write to a collection
- **Read Consistency**: Multiple agents can read concurrently
- **Optimistic Updates**: If a write conflicts, the update function is retried
- **Versioning**: Each store object has a version for conflict detection

## API

```typescript
interface ContextStore {
  // Read operations
  get(collection: string): Promise<any>;
  query(collection: string, predicate: (item) => boolean): Promise<any[]>;
  
  // Write operations
  update(collection: string, updateFn: (current) => updated): Promise<void>;
  
  // Event subscription
  onUpdate(collection: string, handler: (change) => void): Unsubscribe;
}
```

## Adding New Collections

1. Define the TypeScript interface in a new file (e.g., `my-collection.ts`)
2. Export it from `index.ts`
3. Initialize it with empty state
4. Document what agents read/write it
5. Update team contracts README

## Testing

Tests can set up context with specific state:

```typescript
beforeEach(async () => {
  contextStore = new InMemoryContextStore();
  
  await contextStore.initialize({
    'active-requirements': { requirements: [...], ... },
    'active-specs': { specs: [...], ... },
    // ... other collections
  });
});
```
