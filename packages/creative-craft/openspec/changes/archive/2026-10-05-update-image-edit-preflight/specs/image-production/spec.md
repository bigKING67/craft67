## ADDED Requirements

### Requirement: Image edit text preflight
Image edit dry-run and publication SHALL measure visible text with the same font and layout engine used for export, after all operations and before saving imported assets or a revision. Overflow or a box narrower than its glyphs SHALL reject the batch without changing project files. Preflight SHALL NOT rewrite approved copy, resize text, publish during dry-run or imply visual approval. An isolated explicit unlock operation SHALL remain available without layout measurement so locked legacy content can be repaired.

#### Scenario: Rejected edit leaves the project intact
- **WHEN** a batch imports an asset and introduces text overflow or a narrow text box
- **THEN** both dry-run and publication reject it, and no asset or revision is added

#### Scenario: The completed batch determines text fit
- **WHEN** intermediate operations overflow but the completed batch fits
- **THEN** dry-run and publication succeed with the same document digest
- **AND** invisible text is not measured until made visible

#### Scenario: Repair a legacy locked layout
- **WHEN** an existing project contains locked overflowing text
- **THEN** an isolated unlock remains possible and a subsequent fitting edit can be published
- **AND** an undo that would restore the overflowing visible layout is rejected

#### Scenario: Export still checks layout
- **WHEN** a structurally valid overflowing layout is loaded through general create
- **THEN** export independently rejects it and leaves a failure receipt without output images
