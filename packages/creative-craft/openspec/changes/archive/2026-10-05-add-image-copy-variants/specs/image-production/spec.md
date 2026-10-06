## ADDED Requirements

### Requirement: Shared copy across saved layouts
The image CLI SHALL create a new output set from explicit source revision and digest bindings, applying shared text-only object updates to each selected layout through existing edit validation. Each result SHALL include a self-contained editable project, export and source provenance. The source project SHALL remain unchanged. Input SHALL be bounded to twelve uniquely named variants and one hundred uniquely identified text updates.

#### Scenario: Successful multi-layout copy change
- **WHEN** every selected revision contains editable text objects and the shared copy fits
- **THEN** all layouts export with the same copy and unchanged non-text properties, assets and locks
- **AND** the manifest records source and output document digests

#### Scenario: Failed or cancelled batch
- **WHEN** a binding is stale, an object is missing or locked, text overflows, rendering fails or execution is cancelled
- **THEN** no completed set is reported and this invocation's newly created output is removed
- **AND** the source and any preexisting destination remain unchanged
