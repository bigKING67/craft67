# Contributing

Reverse Craft is currently a personal learning project, but changes should remain reviewable and reproducible.

## Development contract

1. Keep `skills/reverse-craft/SKILL.md` as the only discoverable Skill entrypoint.
2. Add specialist guidance to the existing family reference; do not create nested Skills.
3. Preserve the browser67 canonical-runtime boundary for JavaScript/browser sessions.
4. Add or update route-bank cases when routing behavior changes. Do not weaken a collision test to make it green.
5. Update schema, runtime, tests, and docs together when a public CLI/entity contract changes.
6. Record upstream commit, license, path, hash, and classification for reused/adapted mechanisms.
7. Never commit credentials, live cookies/tokens, malware payloads, personal browser data, or runtime case artifacts.

Run before a pull request:

```bash
npm run check:all
python3 /path/to/skill-creator/scripts/quick_validate.py skills/reverse-craft
```

Run real-host and browser gates separately when the required authenticated host/runtime is available; attach only
sanitized receipts, not raw session output.

