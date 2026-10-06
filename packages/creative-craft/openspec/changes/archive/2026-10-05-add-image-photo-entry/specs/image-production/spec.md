## ADDED Requirements

### Requirement: Native-size photo project creation
The optional image CLI SHALL accept a minimal local photo brief and create a normal editable project with a locked photo and independently editable text. The photo SHALL retain its full normalized sRGB pixel region at native oriented dimensions, without cropping or scaling; the original encoded asset SHALL also be preserved.

#### Scenario: Opaque product photograph fits the canvas
- **WHEN** a valid brief supplies a project ID, absolute local opaque photo path and headline
- **THEN** the command creates a revision-one project with bound assets and font, a default 1280 by 1600 white canvas unless dimensions are specified, and a 320-pixel text header
- **AND** existing read, render, edit and undo commands operate on that project

#### Scenario: An input cannot meet the preservation contract
- **WHEN** the photo does not fit below the header, contains non-opaque pixels, or fails existing raster/path validation
- **THEN** creation fails without publishing a project or silently altering the input

### Requirement: Photo brief preflight
The entry SHALL validate the brief, font glyphs and actual text layout before project publication. A dry-run SHALL perform these checks and return the planned document and digest without writing files or making model requests.

#### Scenario: Successful dry-run
- **WHEN** a valid brief is planned for a new destination
- **THEN** the destination remains absent and existing files remain unchanged
- **AND** an unchanged subsequent create produces the same document digest

#### Scenario: Invalid layout or occupied destination
- **WHEN** unknown fields, missing glyphs, text overflow or an existing destination are supplied
- **THEN** dry-run and creation fail, preserving the destination and source files
