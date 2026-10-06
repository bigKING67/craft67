# Craft detail guidance: controlled browser evaluation

Date: 2026-09-19. Baseline repository commit: `8762cbe`.
Decision: **PASS for the bounded fixture; real-product and independent-agent
effectiveness remain UNVERIFIED.**

Later application evidence: [New Money console](new-money-console-2026-09-19.md)
records bounded use on an existing product and a fresh-session read-only check.
It does not replace this fixture's historical verdict, prove every selected
Craft concept on that product, or establish causal Skill improvement.

## Scope and authority

The runnable original fixture is `evals/fixtures/craft-details/index.html`;
its adjacent `DESIGN.md` owns product context, tokens and geometry. No
production project, upstream demo, installed Skill or global route config was
changed. Before mode deliberately seeds defects; it does not show defects
discovered in a real product or prove that old Skill guidance caused them.

Actual skills: skill-creator for reference maintenance; source design-craft for
component implementation and visual/system review; browser67 for runtime.
Route: L1-V, normal risk, web, main_serial; explicit fixture DESIGN authority;
preflight passed after adding the required semantic section headings. No
subagent was used. Screenshots are optional in this component route but were
captured and reviewed for this comparison.

## Source binding

| Input | SHA-256 |
| --- | --- |
| `skills/design-craft/SKILL.md` (unchanged) | `4bb60dcb6c891c2ce97ed1109ba94280edda48a5702314fc1524888615b85e62` |
| `skills/design-craft/references/design-system-contract.md` | `5e528dd46e10e8e135f1c5a92955eb465bdb6e5e143cbb05f435a979b46c11e5` |
| `skills/design-craft/references/source-map.md` | `36a7703b50383e9ea3ddbc46835f7dd5cae1ffb8481d36aa378f1534ed39f726` |
| `evals/fixtures/craft-details/index.html` | `34d1fd4706c30e381dc43abf79b57463a140f90ad5be8235e95a04949798417b` |
| `evals/fixtures/craft-details/DESIGN.md` | `3433a8e636b967a575bdc60446442779cd0e496316f02cd602dc585731f6ade4` |

These bind the working-source instructions and fixture, not a released or
installed version. Prior source-bound certification is not renewed by this case.

## Observations and visual decision

| Check | Observed result |
| --- | --- |
| Canvas / theme | Before dark mode retained a white exposed canvas; after root resolves to rgb(23,27,28) in dark and rgb(244,243,239) in light, matching surface tokens. Existing theme-color updates to #171b1c / #f4f3ef. Browser chrome tint itself is unverified. |
| Corners | Outer 24px radius with 2px border + 10px padding yields a rendered 12px inner radius in after mode versus 24px before. The dark comparison visibly improves the corner gap. |
| Image edge | After light mode separates white media from its white panel with a quiet inner edge. Wrapper pseudo-element is pointer-events:none. Browser CDP pointer press/release at the visible media center activated Open media preview (counter 3 -> 4). |
| Optical correction | Only this triangle moves +2px; the square remains untransformed. It appears better balanced within the same circular control. This is a fixture-specific judgment, not a general rightward-offset rule. |
| Layout invariance | At 1100x850, card/media/play rectangles are exactly identical before and after. Play remains 48x48. Four after captures (two themes x two sizes) report no horizontal overflow. |
| Keyboard | Focused native play button activated once with Enter (1 -> 2) and once with Space (2 -> 3) using CDP keyDown/keyUp with text. An earlier combined dispatch omitted Enter text and yielded only one activation; that incomplete stimulus is not treated as two-key proof. |
| Focus | Both themes show an external 3px focus ring; light rgb(23,92,206), dark rgb(145,188,255). Media decoration does not replace the control focus style. |
| Text size | Root font-size 200% resolves to 32px. At a 390x844 viewport, full content is 390x1103 with no horizontal overflow; labels wrap and controls remain visible. This is text-size simulation, not browser zoom. |

Main-agent visual review: accept the refined fixture. The main content,
hierarchy, spacing, status region and controls remain intact. The light image
edge is clearer; the dark canvas no longer exposes a white field; nested gaps
are more consistent. Same-state play/stop siblings retain identical target,
border and focus grammar with a justified glyph-specific offset. No new motion,
loading, disabled, error, destructive or network states are introduced, so
those axes are not applicable to this offline fixture. This is not a blind
comparison or independent-agent evaluation.

## Screenshot artifacts

Runtime: browser67, one agent-created managed Chrome tab in an existing
dedicated Agent window. Page visibility was hidden; static PNGs were inspected
by the main agent. No foreground/focus lease, smoothness, touch or hardware
claim is made.

Artifact root: `~/.browser67/runtime/runs/design-craft-craft-details/`.
Every capture verified its requested viewport and PNG dimensions, then cleared
the temporary emulation override. The 200% text capture is full-page at a
390x844 viewport; its PNG is therefore taller. Artifacts are external runtime
evidence subject to retention, not distributed package assets.

| Case | PNG dimensions | SHA-256 | Path relative to artifact root |
| --- | --- | --- | --- |
| Before / light / desktop | 1100 x 850 | `ca04dd87e80e1d00cc6a97b26492e41ba1ccafce3642eef116cd68f791683fd2` | `20260919T083747865Z-c828ba57/artifacts/screenshot-viewport-craft-before-light-desktop-20260919T083747870Z-5ceb096c.png` |
| Before / dark / mobile | 390 x 844 | `73ed70f56deb8ac69b240b13ab298aafff96183bfd7a667d00619e9ec0d0a776` | `20260919T083810959Z-5193e055/artifacts/screenshot-viewport-craft-before-dark-mobile-20260919T083810962Z-8638c1c5.png` |
| After / light / desktop | 1100 x 850 | `91a48ee88822818758a4cb5c434001fabdcb55a3dabfc0c7bc11fb5cc8ae432a` | `20260919T083915333Z-68a1c9b3/artifacts/screenshot-viewport-captureAfterLightDesktop-20260919T083915335Z-8c3a24c8.png` |
| After / light / mobile | 390 x 844 | `0968585fa7904d549d641ba6895b4b6e64e20c7e07db1e8361c1081774f4aeae` | `20260919T083915393Z-2441504c/artifacts/screenshot-viewport-captureAfterLightMobile-20260919T083915395Z-bda07e96.png` |
| After / dark / desktop | 1100 x 850 | `66b8cf66add55660d55950d4a6dbc357fcf384c6cba72d1f231040bb2da32427` | `20260919T083831660Z-60b9b46a/artifacts/screenshot-viewport-captureAfterDarkDesktop-20260919T083831662Z-c7514e2f.png` |
| After / dark / mobile | 390 x 844 | `0e2468a389366ab2b0d80648b87b915fa5a62a011e8b863eae33429579e0c799` | `20260919T083831603Z-56d7344c/artifacts/screenshot-viewport-captureAfterDarkMobile-20260919T083831606Z-456b5987.png` |
| After / light / keyboard focus | 390 x 844 | `d8a87a5bc9cc9d03f781d729d4af55d44b06541dd16ddca473010c37c0825b50` | `20260919T083956017Z-be73a35d/artifacts/screenshot-viewport-craft-keyboard-focus-light-20260919T083956019Z-a4168d98.png` |
| After / dark / keyboard focus | 390 x 844 | `e132f90daf2100f0f6d52de36568a5de3a05dc5a3a299544a50c77e31a99a184` | `20260919T084043877Z-0c1338f6/artifacts/screenshot-viewport-craft-keyboard-focus-dark-20260919T084043880Z-875716cf.png` |
| After / dark / 200% text | 390 x 1103 | `cbb15ed1a7845d7484e3067d0b83a87faa0293aa8cd9c57807df0ab9eff6923d` | `20260919T084043991Z-d15fe838/artifacts/screenshot-full_page-craft-dark-text-200-20260919T084043993Z-d7b14ee1.png` |

## Reproduction and checks

Run `PYTHONDONTWRITEBYTECODE=1 python3 -m http.server 8769 --bind 127.0.0.1 --directory evals/fixtures/craft-details`
from the repository root. Open the loopback page through the approved browser
runtime. Query parameters `variant=before|after` and `theme=light|dark`
select the initial state; the two toggle controls exercise transitions.
Use 1100x850 and 390x844 viewports. Focus play and dispatch genuine browser
keyboard input; DOM synthetic KeyboardEvents are not native activation proof.

- Skill quick validator: passed in an isolated uv environment with PyYAML 6.0.3.
  Initial system-Python attempt lacked PyYAML; the offline uv attempt lacked a
  cached wheel. No global Python dependency was modified.
- `PYTHONDONTWRITEBYTECODE=1 make lint`: passed.
- `PYTHONDONTWRITEBYTECODE=1 make validate-portable`: passed all 25 gates,
  including package boundary, source tests and development maturity.
- No text-matching tests or new validation framework were added for these
  original prose additions. Existing gates and rendered behavior are the
  relevant checks.

## Limits and cleanup

Safari/iOS overscroll, browser chrome tint, true browser zoom, touch devices,
screen-reader announcements, RTL/mirrored icons and broad image populations
remain unverified. No conclusion about overall Skill quality or independent
model improvement follows from one deliberately constructed fixture.

Same-instance scoped finalize closed and verified the one task-owned tab:
closed=1, verified=1, kept=0, remaining_unkept=0, errors=0. No user tab was adopted
or closed. The existing Agent window was reused and was not a cleanup target.
The task-owned loopback server was stopped after browser work. No install,
commit, push, version change or release was performed.
