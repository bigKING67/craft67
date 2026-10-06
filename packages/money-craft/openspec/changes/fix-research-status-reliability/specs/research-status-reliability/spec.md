## ADDED Requirements

### Requirement: Unknown evidence is not support
New tracking assessments SHALL distinguish unknown evidence, watch conditions and known adverse evidence. Any UNVERIFIED hypothesis or red line SHALL yield a null score. Known adverse conditions SHALL retain their severity even when evidence is incomplete.

#### Scenario: A hypothesis is unverified
- **WHEN** the recorded hypothesis is UNVERIFIED and no known adverse condition exists
- **THEN** new health output is UNVERIFIED with a null score, not SUPPORTED with ten points

#### Scenario: Red line is watched
- **WHEN** hypotheses are supported but a red line is WATCH
- **THEN** output is WATCH rather than SUPPORTED; damage deductions are not invented for watch conditions

### Requirement: Current assessment is distinct from sealed history
Tracking status SHALL verify artifact integrity and recompute current interpretation. It SHALL preserve sealed v1 bytes and historical verification while using v2 health semantics for current assessments.

#### Scenario: The review window is absent or expired
- **WHEN** a verified thesis has no explicit due_date, lies in the future or is past its registered review deadline
- **THEN** current score is null, historical SUPPORTED becomes UNVERIFIED and freshness states the specific limitation

#### Scenario: The pointer has been altered
- **WHEN** current health values disagree with the verified manifest
- **THEN** status reports invalid integrity and does not offer a current healthy score

### Requirement: Calculation failure is visible
Nonfinite inputs, invalid tolerances and decimal arithmetic failures SHALL produce failed calculation audits instead of success or uncaught arithmetic errors.

#### Scenario: Finite inputs overflow
- **WHEN** calculation exceeds the decimal context's supported range
- **THEN** the audit reports a calculation error and cannot pass

### Requirement: Research citations bind to evidence
Formal research report and thesis citations SHALL bind to successful provider captures or imported official evidence. Local evidence paths SHALL match the corresponding source record. Citation validity SHALL NOT imply semantic support or freshness.

#### Scenario: A document invents a source ID
- **WHEN** a report and its source index agree on an ID absent from run evidence
- **THEN** citation validation fails and completion is blocked

#### Scenario: Provider gaps remain explicit
- **WHEN** a run completes with permitted provider gaps and otherwise valid evidence and documents
- **THEN** completion may describe workflow success while assessment states partial coverage and does not claim semantic support or source freshness
