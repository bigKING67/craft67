# Architecture

## One public Skill

`skills/reverse-craft/SKILL.md` is the only discovery surface. The router selects one of 43 route IDs, and `modules.json`
maps it to one of nine progressive specialist references. Module documents are plain Markdown so Codex/Pi do not load
43 independent Skill descriptions or resolve competing public triggers.

```text
User task
  -> $reverse-craft
  -> deterministic route (R0..R41 plus R44)
  -> one specialist family reference
  -> shared case/evidence runtime
  -> report / rebuilt artifact / verified solution
```

## Installed runtime

The entire dependency-free Python runtime lives under `skills/reverse-craft/lib`; the script entrypoint adjusts only its
process-local import path. This makes a copied Skill work without installing a Python package or npm dependency.

| Component | Responsibility |
|---|---|
| `routing.py` | reviewed 43-route config, regex scoring, artifact magic hints |
| `case_store.py` | private runtime paths, atomic snapshot mutation, portable writer lock, event/report/seal orchestration |
| `case_validation.py` | snapshot/event/seal contracts, artifact fixity, event-chain reconciliation, seal manifest validation |
| `doctor.py` | read-only platform/tool/MCP/browser67 discovery with a secret-safe MCP projection |
| `setup_ops.py` | read-only plan, plan hash, allowlisted explicit apply, durable journal/receipts |
| `provenance.py` | local source-map integrity and optional remote-head drift audit |
| `cli.py` | stable command surface, expected error contract, redacted unexpected-crash diagnostics |

## Runtime data boundary

Source files are immutable inputs. Runtime cases default to `~/.reverse-craft/runs`; setup journals default to
`~/.reverse-craft/setup/transactions`. Tests override the home with temporary directories. No normal command writes to
the Skill/repository.

## JavaScript boundary

Reverse Craft does not implement browser sessions, managed tabs, CDP transport, hooks, or browser evidence storage.
browser67 remains authoritative. Reverse Craft stores only selected browser67 receipt/artifact IDs and hashes in its
cross-domain case graph.

## Trust and recovery

- Runtime-owned case/setup directories are owner-only on POSIX; generated files and copied artifacts are `0600`.
- Atomic JSON snapshot replacement prevents partial documents.
- `events.ndjson` links every event to the previous hash; `case.json` anchors the current count/hash and validation
  reconciles entity events with snapshots.
- Per-case exclusive locks serialize writers and recover only dead/sufficiently stale owners.
- Evidence copies are rehashed after copying; external evidence is rehashed on every validation.
- A seal hashes snapshots, event stream, stored artifacts, and reports; CLI post-seal mutations are rejected.
- Event and seal schemas are checked against runtime field contracts; seal validation also rejects extra fields and
  timestamp drift from the sealed case snapshot.
- Expected CLI errors retain `error.v1`/exit `2`; unexpected exceptions emit `crash.v1`/exit `3` with only the
  exception class, never its message, arguments, environment, or traceback.
- Setup actions are argv arrays, never shell strings. The transaction journal is written before the first process.

These controls provide local consistency and fixity checks. They do not make the run directory append-only at the
filesystem level and do not authenticate an actor who can rewrite the entire case plus its unkeyed seal. Strong
adversarial tamper evidence requires an independently protected digest/signature or external immutable storage.
