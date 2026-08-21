---
description: |
  Spec-Driven Development (SDD) workflow for Claude Code. Use when
  creating medium or large features, significant refactors, migrations,
  architectural changes, or when the user asks for a spec, requirements,
  design, plan before coding, implementation plan, or task breakdown.
  The workflow creates and maintains requirements, design, and tasks as
  versioned Markdown artifacts, enforces approval gates before
  implementation, and requires verification before completion.
name: sdd-workflow
---

# Spec-Driven Development Workflow

## Purpose

Use this skill to prevent implementation by guesswork.

The specification is the source of truth for the work being performed.
The workflow separates discovery, requirements, technical design, task
decomposition, implementation, and verification.

Default approach: **Spec-First**.

For important long-lived features, evolve naturally toward
**Spec-Anchored**: keep the specification in the repository and update
it when the feature changes.

Do not treat SDD as a requirement to write large documents. The
specification must be proportional to the complexity of the change.

------------------------------------------------------------------------

## When to Use

Use SDD for:

-   New medium or large features.
-   Features touching multiple components or layers.
-   Refactors involving multiple files.
-   Architectural changes.
-   Data model or schema changes.
-   API contract changes.
-   Migrations.
-   Integrations with external systems.
-   Changes where multiple agents may work in parallel.
-   Work where explicit acceptance criteria reduce ambiguity.
-   Requests containing terms such as `spec`, `requirements`, `design`,
    `implementation plan`, `plan before coding`, or `tasks`.

### Lightweight SDD

For a small feature, use a reduced workflow:

1.  Short requirements.
2.  Short design.
3.  Implementation.
4.  Verification.

Do not create unnecessary ceremony.

### Do NOT use full SDD for

-   Very small isolated bug fixes.
-   One-line or trivial changes.
-   Simple copy/text changes.
-   Prototypes or exploratory spikes where the goal is learning rather
    than producing maintainable functionality.

If uncertain, prefer a lightweight plan rather than a full
specification.

------------------------------------------------------------------------

# Core Principles

## 1. Plan before coding

Do not write production code while requirements or design are still
ambiguous.

The preferred sequence is:

`Explore → Requirements → Design → Tasks → Implement → Verify`

## 2. Phase gates

Stop after each planning phase and request human approval before
proceeding.

Required gates:

-   Requirements approved before Design.
-   Design approved before Tasks.
-   Tasks approved before Implementation.

Do not silently continue through multiple phases.

## 3. The spec is versioned

Specifications belong in the repository when they provide lasting value.

Recommended structure:

``` text
docs/
└── specs/
    └── <feature-name>/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

For a short-lived Spec-First task, the team may archive or remove the
spec after the implementation is merged.

For important features, keep it as living documentation.

## 4. Behavior before implementation

Requirements describe **what the system must do**, not how it will be
coded.

Prefer testable behavior:

``` text
GIVEN a valid request
WHEN the user submits it
THEN the system creates the requested resource
AND returns a successful response
```

Do not prematurely prescribe classes, functions, libraries, or
infrastructure in requirements.

Those decisions belong in Design.

## 5. Research before decisions

Before writing requirements or design:

-   Inspect the existing repository.
-   Identify relevant modules.
-   Find existing patterns.
-   Identify affected interfaces.
-   Check existing tests.
-   Check project conventions.
-   Reuse existing solutions where appropriate.
-   Identify constraints and dependencies.

Never invent existing architecture.

## 6. Keep specs proportional

Avoid turning SDD into waterfall development.

Prefer several small, independently implementable pieces over one
enormous specification.

Each task should be:

-   Clear.
-   Testable.
-   Bounded.
-   Implementable.
-   Reviewable.
-   As independent as practical.

## 7. Verification is mandatory

Every implementation must have a way to verify its own work.

Depending on the project, verification may include:

-   Unit tests.
-   Integration tests.
-   Type checking.
-   Linting.
-   Build.
-   Static analysis.
-   API tests.
-   End-to-end tests.
-   Browser/UI validation.
-   Data-quality checks.

If the project provides no automated verification, perform the strongest
available validation and explicitly report the limitation.

## 8. Never hide discoveries

If implementation reveals a requirement, constraint, dependency, or
design decision that was not captured in the spec:

1.  Stop the affected work.
2.  Update the relevant specification.
3.  Re-evaluate impacted tasks.
4.  Ask for approval when the change is material.
5.  Continue only after the spec and plan are consistent.

Never let the implementation silently diverge from the specification.

------------------------------------------------------------------------

# Phase 0 --- Repository Discovery

Before generating requirements, inspect the codebase.

Look for:

-   `CLAUDE.md`
-   `README.md`
-   `AGENTS.md`
-   Existing `docs/specs/`
-   Project configuration.
-   Test configuration.
-   CI configuration.
-   Existing architecture documentation.
-   Relevant source files.
-   Existing commands and scripts.
-   Existing skills and agents.

Answer internally:

1.  What already exists?
2.  What is likely to be affected?
3.  What patterns should be reused?
4.  What constraints exist?
5.  What tests already cover the affected behavior?
6.  What is unknown?

Do not modify production code during this phase.

If the repository is large, delegate independent research to subagents
when that improves coverage.

------------------------------------------------------------------------

# Phase 1 --- Requirements

Create:

``` text
docs/specs/<feature-name>/requirements.md
```

Requirements should contain:

## Objective

A concise description of the problem and desired outcome.

## Context

Relevant current behavior and why the change is needed.

## Scope

What is included.

## Out of Scope

What is explicitly not included.

## User Stories / Use Cases

Describe the behavior from the user's or system's perspective.

## Functional Requirements

Each requirement must be specific and testable.

Recommended format:

``` markdown
### FR-001 — <requirement>

The system SHALL <behavior>.

#### Acceptance Criteria

- GIVEN ...
- WHEN ...
- THEN ...
```

## Non-Functional Requirements

Only include requirements that matter, such as:

-   Performance.
-   Security.
-   Reliability.
-   Accessibility.
-   Observability.
-   Scalability.
-   Data quality.
-   Compliance.

## Constraints

Document known technical, business, or operational constraints without
turning them prematurely into implementation decisions.

## Open Questions

List unresolved decisions.

### Requirements quality check

Before asking for approval, verify:

-   No major ambiguity remains hidden.
-   Acceptance criteria are testable.
-   Scope is explicit.
-   Out-of-scope items are explicit.
-   Requirements describe behavior rather than implementation.
-   Important edge cases are identified.
-   Dependencies are identified.

Then STOP.

Ask the user to review and approve the requirements.

Do not generate `design.md` until approved.

------------------------------------------------------------------------

# Phase 2 --- Technical Design

Only start after requirements approval.

Create:

``` text
docs/specs/<feature-name>/design.md
```

The design should explain how the approved requirements will be
satisfied.

Include only decisions that are relevant to implementation.

## Recommended structure

### 1. Architecture

Describe affected components and their responsibilities.

### 2. Components

For each affected component:

-   Responsibility.
-   Inputs.
-   Outputs.
-   Dependencies.
-   Relevant interfaces.

### 3. Data Model

When applicable:

-   Entities.
-   Fields.
-   Relationships.
-   Constraints.
-   Indexes.
-   Migration implications.
-   Data lifecycle.

### 4. APIs / Contracts

When applicable:

-   Endpoints.
-   Request shape.
-   Response shape.
-   Errors.
-   Authentication/authorization.
-   Backward compatibility.

### 5. Data Flow

Describe the flow from input to output.

Use a simple numbered flow or Mermaid diagram when useful.

### 6. State and Error Handling

Describe:

-   Important states.
-   Validation.
-   Failure modes.
-   Retries.
-   Idempotency.
-   Recovery behavior.

### 7. Security

Document relevant:

-   Authentication.
-   Authorization.
-   Secrets.
-   Sensitive data.
-   Input validation.
-   Trust boundaries.

Never include real secrets or credentials.

### 8. Observability

When relevant:

-   Logs.
-   Metrics.
-   Traces.
-   Alerts.
-   Data-quality signals.

### 9. Testing Strategy

Map requirements to validation.

Example:

``` text
FR-001 → unit tests
FR-002 → integration tests
FR-003 → end-to-end test
NFR-001 → performance test
```

### 10. Trade-offs and Alternatives

For important decisions, record:

-   Decision.
-   Alternatives considered.
-   Why the selected approach was chosen.
-   Consequences.

Avoid speculative architecture.

### Design quality check

Verify:

-   Every important requirement has a design response.
-   No design decision contradicts the requirements.
-   Interfaces are explicit.
-   Data changes are identified.
-   Failure behavior is covered.
-   Testing strategy is feasible.
-   Trade-offs are documented where meaningful.

Then STOP.

Ask the user to review and approve the design.

Do not create `tasks.md` until approved.

------------------------------------------------------------------------

# Phase 3 --- Task Decomposition

Only start after design approval.

Create:

``` text
docs/specs/<feature-name>/tasks.md
```

Break the design into atomic implementation tasks.

Each task should include:

``` markdown
### T-001 — <task title>

**Requirement(s):** FR-001
**Depends on:** None
**Parallelizable:** Yes

#### Objective
<what this task accomplishes>

#### Scope
<files/components expected to change>

#### Implementation Notes
<important constraints derived from the design>

#### Verification
<exact tests/checks that must pass>

#### Done When
- [ ] ...
- [ ] ...
```

## Task rules

-   One task should have one clear outcome.
-   Keep tasks small enough to review independently.
-   Include dependencies.
-   Mark tasks that can safely run in parallel.
-   Avoid overlapping file ownership when parallel execution is planned.
-   Do not create tasks that contradict the approved design.
-   Do not add unapproved scope.

### Task quality check

Verify:

-   Every requirement maps to one or more tasks.
-   Every design component that needs implementation is covered.
-   Dependencies are correct.
-   Parallel tasks do not create avoidable conflicts.
-   Every task has verification criteria.
-   Tasks are implementable without guesswork.

Then STOP.

Ask the user to review and approve the tasks.

------------------------------------------------------------------------

# Phase 4 --- Implementation

Only implement after all required phase gates are approved.

The main agent is the **orchestrator**.

Subagents are specialized implementers when parallelization is useful.

## Implementation rules

1.  Read the approved requirements, design, and tasks before coding.
2.  Implement one task at a time unless tasks are explicitly safe to
    parallelize.
3.  Stay within the task's scope.
4.  Do not silently expand scope.
5.  Reuse project conventions.
6.  Write or update tests with the implementation.
7.  Run verification after each meaningful change.
8.  Keep commits atomic when the repository workflow supports it.
9.  Update the spec when material discoveries occur.
10. Review generated code as you would review code from a capable junior
    developer.

## Scope discipline

Before editing a file, confirm it belongs to the task.

If a change outside the declared scope is necessary:

-   Explain why.
-   Identify the affected task/spec.
-   Update the plan when material.
-   Do not sneak the change into the implementation.

## Parallel implementation

Parallelize only when:

-   Tasks are explicitly marked parallelizable.
-   Dependencies are satisfied.
-   Agents will not modify the same files or tightly coupled code.
-   Shared contracts are already defined in the approved design.

Never parallelize merely to be faster.

Consistency is more important than concurrency.

------------------------------------------------------------------------

# Phase 5 --- Verification

Verification is part of implementation, not an optional final step.

Run the strongest applicable checks.

Typical sequence:

``` text
Format
→ Lint
→ Type Check
→ Unit Tests
→ Integration Tests
→ Build
→ E2E / Smoke Test
```

Use the project's actual commands instead of inventing commands.

## Verification report

At completion, report:

-   What was implemented.
-   Tests/checks executed.
-   Results.
-   Known limitations.
-   Any deviations from the spec.
-   Any follow-up work.

Do not claim a test passed if it was not actually executed.

Do not claim an application works merely because the code looks correct.

------------------------------------------------------------------------

# Phase 6 --- Spec Synchronization

After implementation:

1.  Compare the final implementation against `requirements.md`.
2.  Compare it against `design.md`.
3.  Compare completed work against `tasks.md`.
4.  Identify deviations.
5.  Update the spec if the final architecture or behavior intentionally
    changed.
6.  Record important decisions or discoveries.

For long-lived features, the spec becomes living documentation.

For short-lived Spec-First work, archive it according to repository
conventions.

------------------------------------------------------------------------

# Multi-Agent Workflow

When subagents are available, use them deliberately.

## Discovery

Parallel research is encouraged when questions are independent.

Example:

``` text
Agent A → inspect affected frontend components
Agent B → inspect backend/API behavior
Agent C → inspect existing tests and data model
```

The main agent consolidates findings before generating the
specification.

## Implementation

Give every implementation agent:

-   The feature name.
-   The approved requirements.
-   The approved design.
-   The relevant task.
-   Its scope.
-   Verification requirements.

The agent must not invent missing requirements.

If something is ambiguous, it should report the ambiguity rather than
guessing.

## Agent completion contract

An implementation agent should return:

``` text
Task: T-001
Status: COMPLETE | BLOCKED
Files changed:
Tests executed:
Verification result:
Spec deviations:
Notes:
```

------------------------------------------------------------------------

# Human Approval Protocol

Use explicit approval language.

After Requirements:

> Requirements are ready for review. Please approve them before I
> generate the design.

After Design:

> Design is ready for review. Please approve it before I decompose the
> implementation tasks.

After Tasks:

> Tasks are ready for review. Please approve them before implementation.

If the user asks to skip approval, explain that the workflow normally
uses phase gates, but follow the user's explicit decision when
appropriate.

Never pretend approval happened when it did not.

------------------------------------------------------------------------

# Handling Changes During Implementation

If a new discovery is minor and does not alter behavior, document it in
the implementation notes.

If it changes:

-   Requirements.
-   Architecture.
-   API contracts.
-   Data model.
-   Security behavior.
-   Scope.
-   Dependencies.

Then:

1.  Stop the affected task.
2.  Update the relevant spec.
3.  Identify impacted tasks.
4.  Request approval if the change is material.
5.  Resume implementation only after consistency is restored.

This prevents the codebase from drifting away from the source of truth.

------------------------------------------------------------------------

# Boundaries

## ALWAYS

-   Inspect before changing.
-   Use the approved spec as the source of truth.
-   Keep requirements behavior-oriented.
-   Make acceptance criteria testable.
-   Separate requirements from design decisions.
-   Separate design from task decomposition.
-   Verify implementation.
-   Report actual verification results.
-   Keep important specs versioned.
-   Update specs when material discoveries change the plan.
-   Prefer small, atomic tasks.
-   Reuse existing project patterns.

## ASK BEFORE

-   Changing the database schema when it was not approved.
-   Adding a new external dependency.
-   Changing public API contracts.
-   Changing authentication or authorization behavior.
-   Modifying CI/CD architecture.
-   Introducing a new infrastructure service.
-   Changing project-wide conventions.
-   Expanding scope.
-   Deleting data or important existing functionality.

## NEVER

-   Write production code before the required planning gate.
-   Invent requirements.
-   Invent existing architecture.
-   Claim tests passed without running them.
-   Hide deviations from the approved spec.
-   Modify unrelated files without justification.
-   Add credentials, tokens, or secrets to specs.
-   Treat the generated code as automatically correct.
-   Use a huge specification to disguise waterfall development.
-   Force full SDD ceremony onto trivial changes.

------------------------------------------------------------------------

# Recommended Repository Structure

``` text
project/
├── .claude/
│   ├── skills/
│   │   └── sdd-workflow/
│   │       └── SKILL.md
│   ├── agents/
│   │   ├── spec-writer.md
│   │   └── task-implementer.md
│   ├── commands/
│   │   └── spec-new.md
│   └── settings.json
├── docs/
│   └── specs/
│       └── <feature-name>/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
└── CLAUDE.md
```

Keep `CLAUDE.md` focused on repository-wide rules. Keep this skill
focused on the SDD workflow. Do not duplicate the same instructions
across both.

------------------------------------------------------------------------

# Suggested Companion Agents

These are optional. Create them only when they add value.

## spec-writer

Responsibilities:

-   Explore the codebase.
-   Identify affected areas.
-   Turn user goals into testable requirements.
-   Detect ambiguity.
-   Never write production code.

## design-reviewer

Responsibilities:

-   Review requirements and existing architecture.
-   Identify inconsistencies and risks.
-   Challenge unnecessary complexity.
-   Check traceability between requirements and design.
-   Never implement the feature.

## task-implementer

Responsibilities:

-   Implement exactly one approved task.
-   Stay within task scope.
-   Add/update tests.
-   Run verification.
-   Report deviations.
-   Never redefine requirements.

## verifier

Responsibilities:

-   Run relevant checks.
-   Review the implementation against the spec.
-   Identify missing tests or regressions.
-   Report objective verification results.

------------------------------------------------------------------------

# Suggested Command

A project may expose a command such as:

``` text
/spec-new <feature-name>
```

Expected behavior:

1.  Create the feature spec directory.
2.  Invoke this SDD workflow.
3.  Generate requirements.
4.  Stop for approval.
5.  Generate design after approval.
6.  Stop for approval.
7.  Generate tasks after approval.
8.  Stop for approval.
9.  Implement only after approval.

The command is an entry point; this skill remains the workflow source of
truth.

------------------------------------------------------------------------

# Quality Checklist

Before considering an SDD cycle complete:

-   [ ] Repository was inspected before planning.
-   [ ] Requirements are explicit and testable.
-   [ ] Scope and out-of-scope are documented.
-   [ ] Requirements were approved.
-   [ ] Design maps to the requirements.
-   [ ] Important trade-offs are documented.
-   [ ] Design was approved.
-   [ ] Tasks map to requirements and design.
-   [ ] Dependencies are explicit.
-   [ ] Tasks were approved.
-   [ ] Implementation stayed within scope.
-   [ ] Tests/checks were actually executed.
-   [ ] Verification results are reported accurately.
-   [ ] Deviations were documented.
-   [ ] Living specs were synchronized with the final implementation.

------------------------------------------------------------------------

# Reference

This workflow is based on the principles described in:

**"Spec-Driven Development com Claude Code" --- Hack The Task,
20/03/2026**

Key practices incorporated:

-   Spec-First as the practical starting point.
-   Evolution toward Spec-Anchored for important features.
-   Requirements → Design → Tasks → Implementation.
-   Explicit human phase gates.
-   Parallel repository research.
-   Specialized subagents.
-   Atomic implementation tasks.
-   Deterministic verification.
-   Living specifications.
-   Explicit scope boundaries.
-   CLAUDE.md for universal repository rules.
-   Skills for workflow-specific instructions.
-   Hooks for rules that must be deterministic.

Source:
https://hackthetask.com.br/2026/03/20/spec-driven-development-com-claude-code/
