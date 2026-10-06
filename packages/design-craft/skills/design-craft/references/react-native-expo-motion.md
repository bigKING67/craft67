# React Native and Expo motion

Load this reference only when project dependencies or native targets establish
React Native or Expo. A responsive Web page, PWA, or mobile viewport does not
activate it.

## Runtime ownership

- Preserve the project's current animation and gesture stack. Do not add
  Reanimated, Gesture Handler, Skia, or another runtime merely because it is a
  common React Native choice.
- Decide which runtime owns each animated value. Gesture-driven frame updates
  belong on the UI/worklet/native path when the installed stack supports it;
  avoid per-frame React state and bridge callbacks.
- Keep semantic state in React. Keep transient presentation state in the
  animation runtime, then reconcile at bounded lifecycle points.
- Avoid two owners writing the same transform. Compose translation, press
  scale, rotation, and layout movement deliberately or split them across
  wrapper layers.

## Interaction behavior

- Give press feedback on touch-down and preserve cancel-by-dragging-away.
- Start an interrupted gesture from the visible presentation value. Preserve
  measured velocity when settling; target selection remains product-owned.
- Coordinate nested scroll, pan, sheet, and system navigation gestures so one
  recognizer does not silently trap another.
- Trigger haptics only for a causal state transition, selection, boundary, or
  committed action. Haptics supplement visible and accessible feedback; they
  never replace it.
- Bundle Reduced Motion behavior with the motion change. Remove large travel,
  elastic overshoot, parallax, and loops while preserving state feedback.

## Performance and validation

- Keep allocation, synchronous JavaScript work, layout reads, logging, and
  network calls out of frame and gesture callbacks.
- Prefer the project's native transform and layout primitives. Treat any
  library-specific performance claim as a hypothesis until measured in this
  app.
- Validate feel and interruption in a release build on every shipped target.
  An adaptive or cross-platform scope requires both iOS and Android; a
  single-platform scope does not create evidence obligations for an unshipped
  platform. Include a representative slower physical device before making
  final smoothness, haptic, or sustained-performance claims.
- Record runtime/library versions, device or simulator, refresh rate when
  known, Reduced Motion result, and captured video or trace hashes.

There are no universal duration, scale, spring, or GPU guarantees. Calibrate
from product intent, platform convention, installed runtime behavior, and
measured evidence. Static source can establish ownership and likely hot paths;
it cannot prove feel or frame stability.
