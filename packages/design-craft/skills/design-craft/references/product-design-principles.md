# Product design principles

Use these principles to judge whether an interface is product-correct before
judging whether it is visually polished. They apply across web, iOS, Android,
and adaptive products.

## Eight principles

1. **Purpose**: every screen and feature must earn the user's time and
   attention by advancing the primary job.
2. **Agency**: users stay in control through clear choices, reversible actions,
   undo, and confirmations reserved for genuinely destructive decisions.
3. **Responsibility**: privacy, safety, data use, AI uncertainty, and harmful
   failure modes are designed explicitly rather than hidden in policy text.
4. **Familiarity**: platform conventions and learned product patterns provide
   predictability. Depart only when the benefit can be demonstrated.
5. **Flexibility**: the product adapts to ability, expertise, language, device,
   window size, input method, and usage posture without becoming inconsistent.
6. **Simplicity**: remove unnecessary decisions and jargon, not necessary
   context. Progressive disclosure is preferable to hiding everything.
7. **Craft**: alignment, typography, states, motion, performance, and error
   recovery are deliberate and survive real data and long-term evolution.
8. **Delight**: delight emerges from the other principles working together; it
   is not confetti or decorative motion added after the task flow.

## Four human needs

Audit important flows against:

- safety and predictability
- understanding and wayfinding
- achievement and progress
- joy and emotional fit

The dominant need changes by context. A payment confirmation prioritizes
safety; a creative tool may prioritize agency and joy after correctness.

## Operational tests

- **Wayfinding**: can the user answer where they are, what they can do, what
  happened, and how to leave or recover?
- **Feedback**: status, completion, warning, and error feedback arrive at the
  causal moment and name the affected object.
- **Multimodal feedback**: when visual, audio, or haptic channels are supported,
  align them with the same causal state change. Add them only when they improve
  understanding or commitment, respect platform/user settings, and never delay
  one channel merely to meet an unrelated animation-end callback.
- **Mapping**: controls sit near what they affect and use labels specific enough
  to predict the result.
- **Forgiveness**: reversible operations prefer undo; irreversible operations
  explain impact before commit.
- **Platform trust**: a fluent platform user should not pause at off-spec
  navigation, controls, gestures, or accessibility behavior.
- **Context resilience**: interruptions, offline/slow states, long content,
  text scaling, rotation, and window resizing do not destroy the primary job.

## Output contract

When product correctness is in scope, report:

- primary user and job
- principle most at risk
- concrete evidence from runtime or source
- user impact
- smallest corrective design move
- acceptance condition

Do not use these principles as abstract praise. Every finding must connect to a
specific user decision, state transition, or platform behavior.
