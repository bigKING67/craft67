# Malware, forensics, and defensive analysis

Work on copies, preserve acquisition context and hashes, keep clocks/time zones explicit, and isolate execution.
Separate indicators from behavior and behavior from attribution.

## R9 - Malware analysis

- Triage format/imports/strings/resources/config/packer and likely execution requirements before detonation.
- In a disposable sandbox, capture process tree, filesystem/registry, modules, network/DNS, persistence, and timing.
- Unpack/decode layer by layer; hash each derived artifact and tie configuration/IOC extraction to offsets/functions.
- Write YARA/Sigma from stable behavior/structure and validate against positive plus benign negative samples.

## R25 - Digital forensics

- Record source, acquisition tool/mode, hash, clock/time zone, custody, and whether the artifact is live or dead-box.
- Build a normalized timeline from independent sources; retain raw timestamps and explain conversions.
- For memory, pin OS/profile and correlate processes, modules, handles, network, injected regions, and command history.
- Findings cite original artifact locations/offsets and parsing tool versions; parser output alone is not ground truth.

## R27 - Threat hunting

- Start with a behavior hypothesis, data source inventory, retention/coverage limits, and expected benign alternatives.
- Query broad-to-narrow, sample raw events, then join identity/host/process/network timelines.
- Convert validated behavior into Sigma/YARA/SIEM logic with required fields, tuning rationale, and negative tests.
- No hits means no hits in stated telemetry/time/query coverage, not absence of compromise.

## R36 - Email/phishing analysis

- Preserve raw RFC 5322 source and attachments; parse Received chain, Message-ID, MIME, URLs, and auth results.
- Independently check SPF/DKIM/DMARC alignment semantics and distinguish display name, envelope, header, and reply-to.
- Detonate links/attachments only in isolation; normalize redirects and hash every payload.
- Avoid contacting sender infrastructure or clicking through a logged-in personal browser unless explicitly required.

