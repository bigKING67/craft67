# Provider profiles

Provider profiles isolate current model facts from the model-agnostic creative
method.

Each profile must contain:

- stable profile schema;
- provider and model;
- verification date;
- official sources;
- current capabilities and limits;
- known limitations;
- execution availability;
- migration notes.

A profile is evidence, not permission. The user, project authority, rights,
channel rules, and provider policy remain higher constraints.

Do not hardcode a provider fact in `SKILL.md` unless it is timeless. Update the
profile, CLI validation, tests, examples, and changelog together.

Execution surfaces under `surfaces/` are separate contracts. A model profile
describes what the model can do; a Surface Profile describes where and how that
capability is exposed, whether it is currently available, and which execution
modes are verified. Never treat `openai.responses_image_tool` as a simple model
field or infer a future Seedance API contract from Jimeng/Doubao UI behavior.
