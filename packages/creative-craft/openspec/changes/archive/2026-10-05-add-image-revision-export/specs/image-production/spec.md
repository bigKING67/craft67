## ADDED Requirements

### Requirement: Read-only historical image export
The image CLI SHALL accept a trailing `--revision <positive-integer>` on `render` and `preview`. It SHALL use the existing renderer and bind the selected revision and digest in its receipt without modifying project files, active revision or object locks. Omitting the option SHALL retain current-revision behavior. Invalid syntax, nonexistent revisions and extra arguments SHALL fail before creating an output directory.

#### Scenario: Export a saved layout
- **WHEN** a project with later edits is rendered or previewed with an existing earlier revision
- **THEN** it exports that revision's canvas and objects, with the corresponding receipt binding
- **AND** the complete project file tree is unchanged

#### Scenario: Default export
- **WHEN** no revision option is supplied
- **THEN** the current revision is exported

#### Scenario: Invalid revision or arguments
- **WHEN** a revision is malformed, nonexistent, omitted after the flag, duplicated or supplied to another command
- **THEN** the command fails without changing project files or creating output
