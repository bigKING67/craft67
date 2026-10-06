## ADDED Requirements

### Requirement: Explicit business drivers
The core SHALL model segment revenue in one dimension and reconcile historical revenue and parent earnings before calculating scenarios.

#### Scenario: Mixed dimensions
- **WHEN** product and channel segments are added together
- **THEN** the model rejects the input

### Requirement: Auditable assumptions and sensitivities
Every scenario driver SHALL carry rationale, evidence, confirmation and invalidation conditions and next evidence; sensitivities SHALL change one driver at a time.

#### Scenario: Missing invalidation condition
- **WHEN** a driver lacks a falsification condition
- **THEN** the model rejects the scenario

### Requirement: Preserve uncertainty in actual review
The core SHALL expose order-dependent arithmetic contributions and unexplained residuals without claiming causal proof or automatically updating a thesis.

#### Scenario: Actual earnings do not reconcile
- **WHEN** reported earnings differ from the supplied actual-driver model
- **THEN** the residual remains visible and requires research

### Requirement: Bind separately sealed model artifacts
The baseline verifier SHALL verify declared linked model hashes without rewriting old previews.

#### Scenario: Linked model changes
- **WHEN** a model file differs from its sealed hash
- **THEN** baseline inspection fails
