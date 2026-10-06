# Integration Boundaries

## Host-native review

Prefer the host's ordinary review for a bounded PR, commit, branch range, or working
tree change. Review Craft v0.7 reserves its canonical workflow for broader or
higher-assurance work.
Compare the workflows only on matched scope, revision, model, reasoning, and output
constraints. Do not infer superiority from Review Craft's self-score.

## Design Craft

Use Design Craft when the primary question is visual hierarchy, product UI/UX,
motion, interaction, accessibility presentation, design systems, or browser/native
visual evidence. Review Craft may inspect frontend architecture and measured runtime
performance, but it should not replace visual judgment or screenshot validation.

## Host-native security workflow

Use the host's dedicated security workflow for threat models, vulnerability discovery,
source-to-sink paths, exploitability, attack-path analysis, PoCs, severity, and security
fix verification. Review Craft may flag a candidate for escalation and may later import
structured results. Imported results must preserve finding identity, severity,
confidence, and provenance. Review Craft must not weaken or silently reinterpret a
validated security finding.

Evaluate integration fidelity rather than claiming that a general engineering review
is a stronger security scan.
