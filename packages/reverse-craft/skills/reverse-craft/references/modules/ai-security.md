# R14 - LLM and agent security

Model the complete agent system, not just prompt text: system/developer/user inputs, RAG, memory, tools, browser/code
execution, credentials, approval gates, model routing, output sinks, and telemetry.

## Workflow

1. Define protected assets, actor capabilities, trust boundaries, and allowed test content.
2. Build a prompt/tool trace with message roles and transforms. Treat retrieved pages/files/tool output as untrusted data.
3. Test one class at a time: direct/indirect injection, instruction hierarchy confusion, data exfiltration, tool argument
   manipulation, excessive agency, memory poisoning, unsafe rendering, model/supply-chain drift.
4. Use inert canaries and sandbox tools; avoid real secrets and external side effects.
5. Verify controls at the enforcing boundary: allowlists, structured arguments, provenance, confirmation, isolation,
   redaction, and postcondition checks.
6. Retest with paraphrases and benign negatives. Record model/runtime/version because behavior drifts.

## Evidence

Preserve input fixture, message/tool trace, policy/config snapshot, expected versus actual decision, side-effect receipt,
and environment/model identity. A model response saying it would act is not proof that a tool or external mutation occurred.

## Reporting

Separate prompt behavior, tool-call authorization, tool execution, and downstream impact. State stochastic sample count and
do not generalize one hosted-model result to other models/versions.

