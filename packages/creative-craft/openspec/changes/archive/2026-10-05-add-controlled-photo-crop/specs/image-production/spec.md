## ADDED Requirements

### Requirement: Explicit source-bound photo cropping
The CLI SHALL accept crop-photo with a new output directory and input containing an absolute source path, original SHA-256, integer crop rectangle, and declared user authorization with context. Coordinates SHALL refer to the EXIF-oriented sRGB image. The tool SHALL preserve original bytes and normalized pixels, crop without resampling, verify retained RGBA pixels, and write a receipt binding source, rectangle and outputs. It SHALL NOT infer user permission or automatically select white margins.

#### Scenario: Valid crop and preflight
- **WHEN** an authorized, correctly bound rectangle is fully inside the source
- **THEN** dry-run returns the same crop digest as execution without creating output
- **AND** execution preserves original and normalized source with a crop consumable by existing photo templates

#### Scenario: Invalid request
- **WHEN** authorization is absent, source digest mismatches, coordinates are fractional or out of bounds, or output already exists
- **THEN** the command fails without changing source or existing output
