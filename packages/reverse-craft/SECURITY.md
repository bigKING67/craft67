# Security policy

Do not open a public issue containing a credential, reusable exploit against a non-fixture target, private artifact,
malware payload, or sensitive browser/session evidence. Use GitHub private vulnerability reporting for this repository.

Reverse Craft's setup executor accepts only generated plans, canonical SHA-256 confirmation, supported platform/package
catalog entries, and explicit `--yes`. A bypass of these constraints, a case path traversal, seal/fixity bypass, secret
exposure, or unintended target mutation is considered a security defect.

Reports should include the affected commit/version, minimal inert reproducer, expected versus observed boundary, and
whether any secret or external state was exposed. Rotate any credential accidentally included before reporting it.

