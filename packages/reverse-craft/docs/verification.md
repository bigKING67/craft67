# Verification model

Reverse Craft keeps evidence tiers separate:

1. **Source validation**: structure, versions, JSON parseability, route/module completeness, event/seal schema-runtime
   field parity, provenance hashes, Python compile.
2. **Unit behavior**: path safety, private file modes, artifact fixity, event-chain tail anchors, snapshot/event
   reconciliation, malformed-data fail-closed behavior, seal shape/timestamp reconciliation, redacted crash diagnostics,
   MCP secret projection, concurrency, seal, setup tamper rejection.
3. **Routing bank**: manually curated English/Chinese prompts across all 43 routes, including priority/exclusion cases.
   The runner receipt is authoritative for the exact current case count; contract tests enforce the maintained minimum
   coverage floor separately.
4. **Offline scenarios**: curated isolated end-to-end cases through route -> evidence -> finding -> path -> report -> seal.
   The runner receipt is authoritative for the exact current scenario count; the runner enforces the maintained minimum
   coverage floor separately.
5. **Real hosts**: Codex and Pi explicitly invoke an isolated copy of the real Skill for realistic planning requests.
   Their prompts and output schema omit the expected semantic values; the runner validates responses against a private
   R3/browser67, R44/CTI, or R0 bounded-replanning contract and binds the receipt to the prompt, profile-specific schema,
   Skill entrypoint, version, and full source-bundle hash. Exact fields stay exact except for documented bounded aliases.
   R44's source-authority field narrowly normalizes the two source-bounded raw phrases `Web search` and
   `normal Web search` to canonical `Web search`. R0's progress record likewise normalizes only `hypothesis` and
   `current hypothesis` to canonical `current hypothesis`; no other spelling or phrase is accepted.
   Receipts preserve both raw and normalized payloads and their hashes. The private expected contract, including its
   alias map, has its own SHA-256 without being exposed to the Host. Skill identity is a runner-observed fact, not a
   model-graded guess. The Host contract covers
   route, full module reference, runtime/source authority, mutation posture, and evidence-chain order. The R0 profile
   separately compares the checkpoints before and at both bounded progress-stall thresholds, then requires R0 to remain
   primary, the exact pre-replan record, the named gate, and a changed plan dimension. It does not prove that a real
   target can progress or that a proposed tool is feasible. Executable first actions belong to the next runtime-specific
   tier because availability changes the correct action.
6. **Live browser runtime**: pinned browser67 process executes MCP `initialize -> tools/list -> tools/call`, sees 60 tools,
   opens a scoped managed fixture tab, records evidence, exports a rebuild bundle, and finalizes the task.
7. **CI portability**: source/unit/route/scenario gates on Python 3.10 and 3.13 across macOS, Ubuntu, and Windows.

Passing a lower tier does not imply a higher tier. In particular, CI does not prove the user's current browser extension
or authenticated host, and an MCP surface-only check does not prove managed-tab lifecycle.

## Commands

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/run_route_bank.py
python3 scripts/run_scenario_bank.py
python3 scripts/run_host_eval.py --host all
python3 scripts/run_host_eval.py --host all --profile r44
python3 scripts/run_host_eval.py --host all --profile r0-replan
python3 scripts/run_host_eval.py --profile r44 --regrade-receipt /path/to/source-receipt.json
python3 scripts/run_host_eval.py --profile r0-replan --regrade-receipt /path/to/source-receipt.json
python3 scripts/check_browser67_mcp.py --surface-only
python3 scripts/check_browser67_mcp.py
```

Host and browser67 commands are intentionally outside `check:all`: they depend on authenticated/local runtimes and must
be reported as live evidence with host versions and current pins. Each host/profile runs once without success-selecting
retries. Pi receives only its read-only file tool; Codex runs in a read-only sandbox. Both may load Skill instructions
and references, which is required by their progressive-disclosure Skill model. The host receipt proves real process
execution, a content-bound Skill snapshot, and blind semantic output-contract compatibility; it does not replace a live
browser lifecycle or a real public-source intelligence case.

`--surface-only` performs MCP `initialize`, `tools/list`, and read-only browser health only. It never runs orphan
cleanup, creates/adopts/closes a tab, records evidence, exports a rebuild bundle, or calls `finalize_task`; its receipt
reports `orphan_cleanup.status=not_requested`. The full browser67 gate may close only an exact stale Reverse Craft
localhost fixture before creating its own managed fixture. It then records evidence, exports the four-file rebuild
bundle, and requires scoped finalization with zero close errors. Neither mode adopts or closes unrelated user tabs.

`--regrade-receipt` never calls a Host. It is only for correcting a private grader label after a real run: the source
receipt's profile, prompt hashes, response-schema hash, Skill identity, per-Host invocation hashes, snapshots, exit
codes, and raw payloads must still match the current candidate. The regrade preserves the source failure/errors and raw
payload, records the bounded normalized payload separately, binds the corrected private contract hash, and fails closed
on any Host-visible drift or non-allowlisted payload mismatch.
