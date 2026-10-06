## ADDED Requirements

### Requirement: Owned core and explicit source roles
The repository SHALL document Skill and application as consumers of one owned research core, with optional providers and separately classified upstream references.

#### Scenario: Reference is registered
- **WHEN** a project or documentation source is added to the reference registry
- **THEN** its purpose, tracked scope, license status, observation and review/adoption state are recorded without adding a runtime dependency

### Requirement: Immutable review and adoption boundaries
Checks SHALL NOT mutate source locks, adoption mappings or reviewed baselines. Legacy AI Berkshire provenance and default CLI behavior SHALL remain compatible.

#### Scenario: Upstream branch advances
- **WHEN** a live branch differs from the reviewed revision
- **THEN** the checker reports pending review and available scoped file deltas without advancing the reviewed or absorbed revision

#### Scenario: Only cached observations are available
- **WHEN** a multi-source check runs without live retrieval or a fresh complete document capture
- **THEN** it does not claim that all selected sources are current

#### Scenario: Fresh retrieval returns to the reviewed version
- **WHEN** a different observed revision is already pending review and fresh retrieval returns the reviewed revision
- **THEN** the pending observation remains visible and cannot be cleared automatically

### Requirement: Complete document comparison
Document snapshots SHALL bind a complete catalog to canonical URLs, final URLs, titles and semantic-preserving captured-article hashes. Stored baselines SHALL contain metadata rather than copied third-party article bodies.

#### Scenario: Catalog or article changes
- **WHEN** a complete capture adds or removes catalog entries, changes article content/title, or changes an in-scope final URL
- **THEN** the corresponding change is reported for review

#### Scenario: Capture is incomplete or stale
- **WHEN** a page fails, redirects outside scope, lacks an article, or the catalog does not close
- **THEN** the source is unavailable and no deletion or current conclusion is inferred
- **WHEN** an otherwise unchanged capture is older than 24 hours
- **THEN** it is reported as stale rather than current

#### Scenario: Structure carries meaning
- **WHEN** table cell boundaries, code block boundaries or code literal whitespace change
- **THEN** the document fingerprint changes even if flattened visible text would appear identical
- **WHEN** a navigation page nests article cards inside one outer article
- **THEN** the complete outer article is captured once

### Requirement: Per-source failure isolation
Observation failures SHALL remain visible and SHALL NOT prevent independent selected sources from producing results.

#### Scenario: One source is inaccessible
- **WHEN** a selected source fails while another source can be checked
- **THEN** the aggregate result is partial, the other result is preserved, and no review state is mutated

#### Scenario: A capture cannot be identified
- **WHEN** an input capture is unreadable, malformed or lacks a source identity
- **THEN** its error is reported while independent selected sources continue checking

### Requirement: Review coverage and distribution boundary
The initial MyInvestPilot review SHALL account for 149 content/overview pages and six navigation pages, distinguish documentation claims from runtime evidence, and keep full upstream materials outside runtime packages.

#### Scenario: Governance delivery is validated
- **WHEN** repository validation and package checks run
- **THEN** the page inventory matches the review record, existing provenance remains valid, and maintenance documents/scripts and raw third-party bodies are not added to runtime packages
