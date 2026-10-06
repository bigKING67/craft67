# Copy Sheet contract

Read this reference for formal Copy Sheet creation, review, binding, or approval
in Traceable Project. Multiple copy units alone do not require this workflow.
For lightweight writing guidance, use [copy-development.md](copy-development.md).

Use this reference when copy is a material part of a concept, production Job,
adaptation, or delivery. The Copy Sheet is a decision and approval artifact, not
a place to collect disconnected lines.

## Authority order

Build copy from the current project authority:

1. explicit user objective, constraints, rights, and approvals;
2. approved Primary Brand snapshot and projected `BRAND.md`;
3. locked Brief, Creative Direction, claim evidence, legal requirements, and
   channel constraints;
4. selected `OBSERVED` or `INFERRED` Reference principles that cannot override
   brand or project authority;
5. labeled hypotheses to test.

Do not infer a product claim from category convention, a reference, a model
output, or a line that merely sounds plausible. Exact copy, claims, mandatory
elements, and prohibitions remain normative project authority.

## Copy Sheet sequence

### 1. Lock the strategic job

State the objective, audience, tension, proposition, and desired response in
plain language. Each statement needs an evidence state and resolvable `cc://`
references. If the evidence is absent, keep the statement `UNVERIFIED`; if it is
a testable interpretation, keep it `HYPOTHESIZED`.

### 2. Define the voice boundary

Use behavioral voice principles such as "lead with the observable proof" or
"use short declarative sentences." Avoid generic labels such as "premium, bold,
human" unless each label changes a concrete writing decision. Record prohibited
tones so reviewers can reject drift consistently.

### 3. Order proof before writing lines

Rank proof statements by communicative importance. Separate:

- verified product or brand facts;
- directly observed behavior;
- reasoned interpretations;
- performance hypotheses;
- missing evidence.

Copy may simplify supported proof but cannot strengthen its evidence class.

### 4. Develop genuinely distinct copy routes

Each route must have a different job and mechanism, not just different words.
For each route record:

- what communication job it performs;
- how the language creates the intended response;
- what evidence supports the mechanism;
- what result or observation would falsify it.

If one route becomes another by replacing adjectives or sentence rhythm, merge
them and develop a route with a different mechanism.

### 5. Select exact copy units

Each unit records its role, exact text, language, evidence state/references, and
render method. Keep mandatory copy present as exact units. Legal copy must use a
`legal` unit. Prohibited copy is a validation and review boundary, not a source
of rewrite suggestions.

Use the render method deliberately:

- `provider_render`: the generation provider must render the text and output
  inspection must verify every character;
- `post_overlay`: typography is added deterministically after generation;
- `hybrid`: some text is generated and some is overlaid; name the boundary in
  production notes;
- `live_action`: text is captured in physical production and must be inspected;
- `typography_only`: the asset is composed primarily as deterministic type;
- `voiceover`: verify script, performance, pronunciation, timing, and rights;
- `subtitle`: verify wording, timing, safe area, and accessibility.

### 6. Bind Jobs and adaptations

A copy-bound Image/Video Job references one `copy_sheet_id` and only the
`copy_unit_refs` it actually uses. An adaptation should preserve the selected
route and proposition unless a new concept decision is explicit. Channel or
language changes may require a new reviewed Copy Sheet rather than an in-place
mutation of approved history.

## Approval states

- `draft` + `exploration` + pending approval: route exploration only;
- `reviewed` + `internal`: a named reviewer has checked the sheet and internal
  production may become ready;
- `approved` + `public`: a named owner has approved public use with timestamps
  and a concrete basis;
- `superseded`: readable history that cannot govern a new Job.

Public approval is not valid while strategy, proof, routes, or units still use
`HYPOTHESIZED` or `UNVERIFIED` evidence. Approval of one Copy Sheet does not
approve generated output; output inspection and Delivery evidence remain
separate gates.

## Review checklist

- Does every line perform a distinct, named job?
- Is the proposition clear without inventing a claim?
- Does the proof hierarchy match the evidence strength?
- Are mandatory, prohibited, and legal copy complete?
- Are copy routes meaningfully different?
- Are exact units and render methods production-ready?
- Are Job references limited to units actually used?
- Are remaining unknowns explicit?
- Is internal review separated from named-owner public approval?
- Will actual rendered text, voice, or subtitles be inspected before delivery?
