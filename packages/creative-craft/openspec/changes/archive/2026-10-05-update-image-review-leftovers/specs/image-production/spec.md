## ADDED Requirements

### Requirement: Provider claim release before any request
A Provider run that fails before any client POST attempt SHALL remove its job directory and release the job ID; once a POST may have been attempted, the claim SHALL remain and the job SHALL NOT be retried automatically.

#### Scenario: Revision conflict detected before the POST
- **WHEN** the project changes between preparation and the pre-request revision check
- **THEN** no request is sent, the job directory is removed, and the same job can run after the caller re-reads the project

### Requirement: OS path aliases
Path validation SHALL accept OS-owned symlink aliases directly under the filesystem root (such as macOS `/tmp` and `/var`) and SHALL still refuse symlinks at every component below them.

#### Scenario: Project in the system temporary directory
- **WHEN** a project is created and read through the default temporary directory path on macOS
- **THEN** both succeed, while a symlink to that project is refused
