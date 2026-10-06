# image-production Specification

## Purpose

Optional source-checkout image executor (`integrations/image-production`): editable local image projects with revision history, deterministic rendering, photo entry and templates, controlled cropping, shared-copy variants, staged candidates with masked compositing, and an evidence-bound GPT Image Provider adapter. It is a local experimental contract and does not replace canonical Image Job / Receipt / Inspection approval.

## Requirements

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

### Requirement: Shared copy across saved layouts
The image CLI SHALL create a new output set from explicit source revision and digest bindings, applying shared text-only object updates to each selected layout through existing edit validation. Each result SHALL include a self-contained editable project, export and source provenance. The source project SHALL remain unchanged. Input SHALL be bounded to twelve uniquely named variants and one hundred uniquely identified text updates.

#### Scenario: Successful multi-layout copy change
- **WHEN** every selected revision contains editable text objects and the shared copy fits
- **THEN** all layouts export with the same copy and unchanged non-text properties, assets and locks
- **AND** the manifest records source and output document digests

#### Scenario: Failed or cancelled batch
- **WHEN** a binding is stale, an object is missing or locked, text overflows, rendering fails or execution is cancelled
- **THEN** no completed set is reported and this invocation's newly created output is removed
- **AND** the source and any preexisting destination remain unchanged

### Requirement: Reusable purpose templates
create-photo SHALL accept optional brand-detail and xiaohongshu-cover templates with source, headline and brand. It SHALL preserve native photo pixels, place the photo within a proportional slot and produce ordinary editable objects. Existing input without template SHALL retain its current behavior. The template identity SHALL be returned with layout metadata. These layouts SHALL NOT imply platform certification.

#### Scenario: Reuse with another photo
- **WHEN** an opaque photograph of different dimensions fits the slot
- **THEN** it is centered at native scale, remains locked and can be exported with unchanged pixels
- **AND** the exact supplied copy is preserved

#### Scenario: Invalid or insufficient input
- **WHEN** the template is unknown, required brand is missing, unsupported caption is supplied, canvas ratio differs, photo exceeds its slot or text does not fit
- **THEN** dry-run and actual creation fail without publishing a project

#### Scenario: Dry-run and creation
- **WHEN** unchanged valid template inputs are preflighted and created
- **THEN** dry-run writes nothing and predicts the created document digest

### Requirement: Explicit source-bound photo cropping
The CLI SHALL accept crop-photo with a new output directory and input containing an absolute source path, original SHA-256, integer crop rectangle, and declared user authorization with context. Coordinates SHALL refer to the EXIF-oriented sRGB image. The tool SHALL preserve original bytes and normalized pixels, crop without resampling, verify retained RGBA pixels, and write a receipt binding source, rectangle and outputs. It SHALL NOT infer user permission or automatically select white margins.

#### Scenario: Valid crop and preflight
- **WHEN** an authorized, correctly bound rectangle is fully inside the source
- **THEN** dry-run returns the same crop digest as execution without creating output
- **AND** execution preserves original and normalized source with a crop consumable by existing photo templates

#### Scenario: Invalid request
- **WHEN** authorization is absent, source digest mismatches, coordinates are fractional or out of bounds, or output already exists
- **THEN** the command fails without changing source or existing output

### Requirement: Provider-aware transparent jobs
Image Job v2 SHALL accept transparent output only when the selected provider explicitly supports it, with PNG or WebP format. The optional Sunburst/Flare image Adapter SHALL keep its single PNG output rule. Legacy v1 and providers without transparency support SHALL remain rejected.

#### Scenario: Explicit support
- **WHEN** a ready v2 Sunburst or Flare PNG job requests transparent background
- **THEN** validation and dry-run succeed and the request records transparent background

#### Scenario: Unsupported provider or format
- **WHEN** a transparent job uses the legacy provider, v1 or JPEG
- **THEN** it fails before a provider request

### Requirement: Evidence-bound alpha acceptance
Transparent provider output SHALL include an alpha channel, at least one alpha-zero pixel and at least one visible pixel. Received and normalized measurements SHALL bind their respective bytes. An invalid image SHALL be retained with a partial receipt and specific failure code, without candidate publication or automatic retry.

#### Scenario: Opaque or empty output
- **WHEN** a provider returns no alpha, no clear background, or an entirely transparent image
- **THEN** the result is rejected, the original image is retained, and the current project stays unchanged

#### Scenario: Offline normalization
- **WHEN** a retained transparent PNG has a size mismatch
- **THEN** explicit same-aspect recovery revalidates source and normalized alpha, binds both measurements and sends no new request

### Requirement: Composed candidate validation
The image workflow SHALL recheck transparency on the composed candidate during staging and readback, and SHALL retain exact protected-pixel checks. Successful execution SHALL NOT automatically accept a candidate or approve visual quality.

#### Scenario: Protection hides all transparent output
- **WHEN** a valid transparent provider source is composited into a fully opaque result
- **THEN** candidate publication fails while retaining the successful provider output

#### Scenario: Receipt alpha mismatch
- **WHEN** recorded alpha measurements disagree with the bound image bytes or are missing
- **THEN** candidate readback and acceptance fail

#### Scenario: Existing ordinary jobs
- **WHEN** an opaque or auto job is created or a prior ordinary receipt is reopened
- **THEN** it follows its existing behavior without requiring new alpha evidence

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

### Requirement: Photo canvas background
The photo entry SHALL accept an optional explicit `#RRGGBB` canvas background and SHALL report each photo border's mean color and channel spread, without sampling or applying a color automatically.

#### Scenario: Studio photo on a matching canvas
- **WHEN** a brief supplies `background` for a default or template layout
- **THEN** the created project uses that canvas color and existing defaults stay unchanged when it is omitted
- **AND** dry-run and create results include `layout.photo_edges` for top, bottom, left and right
