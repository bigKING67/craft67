## ADDED Requirements

### Requirement: Photo canvas background
The photo entry SHALL accept an optional explicit `#RRGGBB` canvas background and SHALL report each photo border's mean color and channel spread, without sampling or applying a color automatically.

#### Scenario: Studio photo on a matching canvas
- **WHEN** a brief supplies `background` for a default or template layout
- **THEN** the created project uses that canvas color and existing defaults stay unchanged when it is omitted
- **AND** dry-run and create results include `layout.photo_edges` for top, bottom, left and right
