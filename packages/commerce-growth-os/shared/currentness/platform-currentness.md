# Platform Currentness

## Load when

Use this reference when the user asks about latest/current platform capability, ad product functions, platform rules, compliance boundaries, creator cooperation rules, or whether a tactic "still works".

## Rule

Separate stable operating principles from current platform facts.

- Stable operating principles: unit economics, SKU-role design, price-channel separation, content-to-search landing, review quality, fulfillment risk, and repurchase logic.
- Current platform facts: product names, ad campaign types, targeting options, bidding modes, creator tools, traffic entrances, policy wording, eligibility thresholds, and compliance rules.

Do not present a current platform fact as confirmed unless it is verified from an authoritative source or from the user's current backend evidence.

## Required evidence

Use `currentness-official-sources.md` to choose the verification surface and official entry point. A reachable URL proves only entry-point reachability; it does not prove content freshness, account eligibility, or current capability.

## Required labels

Label platform-sensitive claims:

- Confirmed from user backend: user provided current backend evidence.
- Officially verified: checked from official/authoritative source in the current session.
- Stable operating principle: not dependent on a current platform feature.
- Needs current verification: likely to drift and not verified in the current session.

Never hide the verification status inside the prose. Put it near the claim or in a short "Currentness" note.

Verify any product name, entrance, targeting/bidding option, attribution field, fee, eligibility threshold, creator workflow, platform rule, or compliance wording that can change the decision.

## Response pattern

When currentness matters, use a compact note:

```text
Currentness:
- Stable principle: ...
- Officially verified / Confirmed from user backend / Needs current verification: ...
- Decision impact: ...
```

If the user asks for action before verification is possible, give the operating logic and make the platform-specific step conditional:

```text
If the current backend supports this entrance, use it for ...
If not, keep the same channel job and switch the execution surface to ...
```

## Avoid

- Do not say "currently" or "now" for unverified product capabilities.
- Do not quote old platform product names as if the interface still uses them.
- Do not rely on third-party playbooks for compliance or policy boundaries.
- Do not turn a platform workaround into a durable recommendation without verification.
