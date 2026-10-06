# Product context contract

Use this when a project has, needs, or can benefit from an optional
`PRODUCT.md`. `PRODUCT.md` records product intent and platform facts;
`DESIGN.md` remains the only authority for visual language, tokens,
components, themes, and motion.

## Contents

- [Separation of authority](#separation-of-authority)
- [Recommended shape](#recommended-shape)
- [Discovery and confidence](#discovery-and-confidence)
- [Platform meaning](#platform-meaning)
- [Review checklist](#review-checklist)

## Separation of authority

`PRODUCT.md` owns:

- `register`: product, brand, editorial, commerce, developer-tool, or another
  product category.
- `platform`: `web`, `ios`, `android`, or `adaptive`.
- `users`: primary and secondary audiences, expertise, and constraints.
- `purpose`: the user job and outcome the product exists to enable.
- `positioning`: product promise, differentiation, and desired perception.
- `accessibility`: supported assistive technology, text scaling, motion,
  contrast, input, language, and cognitive requirements.

`DESIGN.md` owns:

- visual direction and brand expression
- color, typography, spacing, radii, elevation, and icon tokens
- component grammar and state behavior
- light/dark/high-contrast themes
- motion language and timing primitives
- surface-specific visual rules

Do not duplicate token values or component specifications into `PRODUCT.md`.
Do not put market positioning or user definitions into `DESIGN.md` unless a
visual rule genuinely depends on them.

## Recommended shape

```markdown
# Product Context

## Register
product

## Platform
adaptive

## Users
- Primary: field operators using a phone one-handed.
- Secondary: managers reviewing the same work on tablets and desktop web.

## Purpose
Complete and verify a field task without losing progress when interrupted.

## Positioning
Operationally trustworthy, fast, and calm rather than playful or promotional.

## Accessibility
- VoiceOver and TalkBack labels and traversal are release requirements.
- Dynamic Type and Android font scaling must reach 200% without clipping.
- Reduced Motion replaces large spatial transitions with cross-fades.
- Core flows support touch, hardware keyboard, and switch access.
```

Each heading is optional except when the project depends on that decision. Keep
the file concise and product-specific.

## Discovery and confidence

Resolve platform in this order:

1. Explicit route `--platform`.
2. Nearest `PRODUCT.md` `## Platform` value.
3. Codebase detection.
4. Default `web`.

Resolve an explicit `--product-context-path` before upward discovery. Report:

- resolved path, or an empty path
- source: `explicit`, `product_context`, `codebase`, or `default`
- confidence from `0.0` to `1.0`
- detection signals and contradictions

Implicit `PRODUCT.md` and `DESIGN.md` discovery is project-owned: it stops at
the nearest Git or recognized project boundary, rejects symlinked authority
files, never inherits a home-directory authority, and applies a monorepo-root
authority only when valid workspace metadata includes the target. Present but
invalid, oversized, or symlinked workspace/package metadata fails closed and
must be reported as degraded evidence. An explicit path remains the deliberate
escape hatch when the user wants authority outside that boundary.

Missing `PRODUCT.md` does not block an existing-project task. Infer the minimum
context from source/runtime evidence, report confidence, and suggest creating
the file after the scoped task. New product shaping may create it when the user
has supplied enough facts.

## Platform meaning

- `web`: browser-delivered UI, including responsive web, PWAs, Capacitor,
  Cordova, and WebView shells whose product UI is still HTML/CSS.
- `ios`: a product shipping only through an iOS/iPadOS native target.
- `android`: a product shipping only through an Android native target.
- `adaptive`: one product shipping native UI to both Apple and Android
  platforms, including React Native/Expo, Flutter, Kotlin Multiplatform/Compose
  Multiplatform, or a repository with real iOS and Android targets.

`surface=mobile` is a viewport/form-factor hint, not proof of a native
platform. Never infer native only from the word mobile.

## Review checklist

- Does the resolved platform match what is actually built and shipped?
- Are product requirements separated from visual authority?
- Are user jobs and accessibility constraints concrete enough to change a
  design decision?
- Are inferred values clearly marked with confidence rather than presented as
  confirmed facts?
- If code and `PRODUCT.md` conflict, was live build/runtime evidence checked?
