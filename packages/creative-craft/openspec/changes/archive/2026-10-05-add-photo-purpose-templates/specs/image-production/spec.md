## ADDED Requirements

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
