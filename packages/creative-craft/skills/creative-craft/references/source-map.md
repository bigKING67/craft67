# Source map

Verified: `2026-08-04`.

Provider capabilities change. Use official sources and update the matching
profile, tests, and examples together.

## OpenAI GPT Image 2

Primary sources:

- Model:
  `https://developers.openai.com/api/docs/models/gpt-image-2`
- Image generation and editing:
  `https://developers.openai.com/api/docs/guides/image-generation`
- Official prompting guide:
  `https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide`

Current profile:
`../providers/openai-gpt-image-2.json`

Core facts used:

- Image API supports generation and edit endpoints.
- Responses API supports conversational and multi-turn image workflows.
- GPT Image 2 automatically handles image inputs at high fidelity.
- size, quality, format, JPEG/WebP compression, and opaque/automatic background
  are configurable; transparent output is not currently supported by GPT Image 2.
- masked edits require compatible source/mask assets; the mask is guidance rather
  than a guaranteed pixel-exact boundary.
- prompt structure, intended use, concrete visual description, explicit
  reference roles, change/preserve separation, and small controlled iterations
  are recommended.
- actual text, consistency, and layout-sensitive composition still require
  output inspection.

## ByteDance Seedance 2.5

Project-owner supplied documents:

- User guide:
  `https://bytedance.larkoffice.com/wiki/NjnWwvf4BiFYFLk2RzrcEgaunGf`
- Prompt guide:
  `https://bytedance.larkoffice.com/docx/OsiUdR1OxoDqvnxsK8LczYx7nPd`

Official public sources:

- Model:
  `https://seed.bytedance.com/en/seedance2_5`
- Launch article:
  `https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5`
- Previous architecture/context:
  `https://seed.bytedance.com/en/blog/official-launch-of-seedance-2-0`

Current profile:
`../providers/bytedance-seedance-2.5.json`

Core facts used:

- 30-second single-pass audiovisual generation and multi-round extension;
- multimodal reference input;
- timestamp-oriented generation/editing control;
- reference-based, green-screen, camera-perspective, motion, creative, and clay
  render workflows;
- explicit reference role mapping, timeline design, continuity locks, and
  preserved edit boundaries;
- current public launch information said API access was coming via BytePlus
  ModelArk, so this release does not pretend a stable public API contract exists.

The two Lark documents were supplied as authorities by the project owner. They
must be reviewed manually when updating detailed UI behavior or prompt syntax
that is absent from public model pages.

## Craft family

Content-production engineering research is maintained in repository-only
`docs/upstream-absorption.md`, alongside `docs/content-production-architecture.md`.
Resolve these paths from a Creative Craft source checkout, not from an installed
Skill leaf: repository docs are not bundled runtime instructions. The register
covers HyperFrames, ChatCut Agent Plugin, OpenChatCut, OpenMontage, Remotion,
Cerul, OpenCut and image-engineering references with separate reference and
execution states; HyperFrames
has local-production and limited DataHub integration evidence. Host tests use
isolated storage and, for model paths, a loopback model fixture; they do not
prove cloud-provider, recognition-quality or production acceptance. See the
register for dated scope, evidence locations and planned absorption gates.
Its 2026-09-20 review does not refresh the Provider facts dated
above. Load it for upstream maintenance, not ordinary creative requests.

Repository conventions and method inspiration:

- `https://github.com/bigKING67/design-craft`
- `https://github.com/bigKING67/review-craft`

Creative Craft borrows the principles of scoped authority, canonical runtime,
reference routing, deterministic validation, evidence separation, explicit
decisions, and honest delivery boundaries. It does not copy their product
scope.

## Source policy

1. current official model/API documentation;
2. current official launch or capability article;
3. project-owner supplied official guide;
4. provider product UI;
5. primary technical paper;
6. high-quality secondary source, labeled as secondary;
7. generic practice.

Never promote an indexed snippet or third-party summary into a hard limit when
an official source is unavailable. Record uncertainty in the provider profile.
