# 3D-Craft repository guidance

This repository ships exactly one installable product: `skills/3d-craft/`.
Root-level files exist for development, evaluation, source governance, and
packaging. Do not turn root development infrastructure into runtime
requirements for the installed Skill.

## V0.1 boundary

- Support product and prop assets through Blender, GLB, and a React Three Fiber
  viewer.
- Treat Blender 5.2.1 LTS headless CLI as the canonical automation runtime.
- Use browser67 for real-browser evidence. Do not silently fall back to the
  in-app browser or a user-owned browser profile.
- Keep reference reconstruction, animation, games, WebGPU, and MCP-specific
  automation out of V0.1.
- Do not claim visual, runtime, performance, or host compatibility without the
  corresponding evidence.

## Change discipline

- Preserve `.codex/config.toml` and unrelated work in a dirty worktree.
- Generated Blender, GLB, screenshot, report, cache, and run-state artifacts
  belong outside the repository unless they are deliberately small fixtures.
- Use explicit schemas and stable enumerations for machine contracts.
- Do not commit, push, tag, release, publish, or install globally unless the
  user authorizes that layer separately.
