## ADDED Requirements

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
