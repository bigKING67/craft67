## ADDED Requirements

### Requirement: Preserve dated research baselines
The core SHALL exclusively create local baseline files, verify their hashes and source files, preserve expectation origins, and disclose timestamp assurance.

#### Scenario: Historical reconstruction
- **WHEN** a baseline is locally sealed after actual disclosure
- **THEN** replay labels it reconstructed and does not present it as a contemporaneous forecast

#### Scenario: Existing baseline
- **WHEN** sealing targets an existing file
- **THEN** the operation fails without overwriting it

### Requirement: Evidence-driven replay
The core SHALL reject incompatible fiscal periods and unavailable evidence, require contemporaneous disclosure evidence, and preserve original baselines.

#### Scenario: Catalyst window expires
- **WHEN** a catalyst has no observation after its expected window
- **THEN** it is overdue and unverified, with an open research task

#### Scenario: Event occurs
- **WHEN** a source-bound observation records an occurrence
- **THEN** the event is recorded without automatically confirming an investment thesis

### Requirement: Inspect a pending baseline without actuals
The core SHALL verify a sealed preview and its source files without requiring an outcome, and SHALL distinguish missing outcome input from evidence of nondisclosure.

#### Scenario: No outcome supplied
- **WHEN** a baseline is inspected before an outcome has been entered
- **THEN** integrity and pending research tasks are returned while actual disclosure remains unverified

#### Scenario: Local date crosses UTC midnight
- **WHEN** the host calendar date differs from the UTC date
- **THEN** preview date validation uses the local calendar and disclosure comparison preserves the seal timestamp offset

### Requirement: Evidence-bound numeric corroboration
The core SHALL compare explicitly declared filing inputs with a hash-verified provider capture, preserving date, identity, unit and cumulative-period semantics without rewriting the baseline.

#### Scenario: Different cumulative and standalone periods
- **WHEN** a standalone quarter is checked against an explicitly confirmed cumulative provider series
- **THEN** the core subtracts adjacent cumulative values and records operands

#### Scenario: Missing or conflicting data
- **WHEN** provider data is absent, null, unverified in basis or exceeds difference tolerances
- **THEN** the result is non-passing and does not promote research readiness

#### Scenario: A later provider capture
- **WHEN** corroboration is captured after the baseline seal
- **THEN** its capture time is retained and it is never represented as point-in-time evidence available at the original seal
