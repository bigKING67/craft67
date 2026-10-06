# Landing page evaluation spec

## Prompt

Use `design-craft` to build or redesign a premium landing page for a
developer tool. The page must avoid generic AI SaaS patterns, keep strong
typographic hierarchy, work on mobile, and preserve the project's existing
`DESIGN.md` unless the user explicitly approves evolution.

## Expected route behavior

- `surface`: `landing` or `marketing`
- `intent`: `new-page`, `visual-refine`, or `redesign`
- `scope`: `page` or `multi-page`
- `browser_validation_required`: `true`
- `browser_screenshot_required`: `true` for visual page work
- `candidate_skills` reported separately from actually used skills
- `style_authority_path` read when present

## Expected design-craft references

- `references/visual-judgment.md`
- `references/impeccable-workflow.md`
- `references/engineering-quality.md`
- `references/performance-quality.md`
- `references/validation-contract.md`

## Success behavior

- Starts with a concise design read.
- Audits existing brand/components before replacing them.
- Avoids generic hero plus three cards plus testimonial grid.
- Uses purposeful composition, proof, contrast, rhythm, and readable copy.
- Runs type/lint/build as relevant and browser smoke on desktop and mobile.

## Failure modes

- Treats route candidate skills as actually used.
- Ignores `DESIGN.md`.
- Ships decorative motion that hurts readability or reduced-motion behavior.
- Claims browser validation without a browser tool result.
- Claims screenshot validation without artifact path/hash/dimensions.
