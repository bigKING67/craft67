## ADDED Requirements

### Requirement: Paid Provider result preservation
After a Provider request has been sent, the module SHALL persist receipt evidence and any received output even when out-of-process receipt validation fails, and SHALL offer offline recovery that never repeats the request.

#### Scenario: Receipt validation unavailable after the request
- **WHEN** the response was received but receipt validation fails
- **THEN** `receipt.unvalidated.json` and the received output remain in the job directory and the command fails without retrying
- **AND** `provider-recover` later validates the receipt, promotes it to `receipt.json` and stages the candidate with zero network requests, at most once per job

#### Scenario: Late cancellation
- **WHEN** a timeout or cancellation fires after the complete response body was received
- **THEN** local processing completes and a specific local verdict outranks the abort in the receipt

### Requirement: Outputs outside the project
Render, preview, copy-variants and candidate comparison SHALL refuse any output directory located inside the source project, compared by directory identity.

#### Scenario: Case-variant or nested output path
- **WHEN** the output resolves inside the project, including through a case-variant spelling on a case-insensitive file system
- **THEN** the command fails before creating the output and the project remains readable and unchanged

### Requirement: Recoverable candidate and project state
The module SHALL report damaged candidate entries without failing the whole listing, SHALL release a stale decision lock only through an explicit audited command, and SHALL identify an interrupted project creation.

#### Scenario: Stale decision lock
- **WHEN** a decision lock remains after its holder process exited
- **THEN** `candidate-unlock` with author and summary writes an immutable release record and removes the lock
- **AND** it refuses while the recorded holder process is still running

#### Scenario: Stray or interrupted candidate entries
- **WHEN** the candidates directory contains non-candidate files or a directory without `candidate.json`
- **THEN** listing reports the directory as `incomplete` in place, and non-candidate files do not consume candidate slots
