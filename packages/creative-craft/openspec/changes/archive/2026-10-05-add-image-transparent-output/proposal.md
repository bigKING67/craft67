# Explicit transparent image output

## Why

The real GROLAND trial returned useful alpha, but the canonical v2 job and image Adapter cannot request transparency. Merely allowing the parameter could accept opaque or empty images, or lose alpha during normalization/compositing.

## What Changes

- Permit v2 transparent jobs only with an explicitly capable provider and PNG/WebP. The optional Sunburst/Flare Adapter remains PNG-only. Legacy v1 and GPT Image 2 keep their existing restriction.
- Validate alpha in received and normalized images; require at least one fully transparent and one visible pixel, retain rejected output and a specific partial receipt, and never auto-retry.
- Bind alpha measurements to image bytes; recheck recovery, candidate loading and the composed candidate. Continue deterministic protected-pixel QA and separate visual approval from execution.
- Verify opaque/auto compatibility and replay the saved real product locally. No new model call, runtime dependency, global install, commit or push.

## Impact

Canonical image v2 schema/semantic validator; optional image Provider, receipt readback, candidate checks, regression tests and image docs. No video/UI work. Alpha is a structural check, not proof of glass optics, product identity or creative approval.

## Authorization

2026-10-04: user said “按你建议继续” in direct response to the proposed transparent task protocol, actual alpha checks, protected regions and failure receipts. This records that accepted scope; it does not introduce another approval step.
