# Upstream adoption review — 2026-10-12

## Decision and scope

This bounded adoption decision covers remote movement after [the 2026-10-11 review](upstream-adoption-review-2026-10-11.md): Emil added a Skill, and Taste merged a batch of 29 commits. Impeccable and Jakub had no unreviewed movement. All compatibility pins stay unchanged.

| Upstream | Compared range | Commits / changed paths | Adoption disposition |
| --- | --- | --- | --- |
| taste-skill | [717446e…d237dd3](https://github.com/Leonxlnx/taste-skill/compare/717446e07a78d4e6d7918b1fde1a263378eebac9...d237dd399d57524945c0c81327da5da19f7a468d) | 29 / 10 | `partial` |
| emilkowalski-skills | [e8a175d…2d22863](https://github.com/emilkowalski/skills/compare/e8a175de22ae1e49370fc144c1f3bb9aeedf988d...2d228630ba1446365f614a108cb8252f1feda202) | 2 / 2 | `partial` |

The two paths are a one-line README change and the new 222-line `skills/animation-performance/SKILL.md`, read in full.

## Taste decision

All five changed `SKILL.md` patches were read. Absorbed: the redesign-skill rule that a collapsible sidebar collapses to a usable icon rail, not to nothing. Names stay in the DOM, tooltips appear on hover and focus, targets are 44px, the toggle carries `aria-expanded`, and the rail is never inside an `inert` ancestor. It is now in the dashboard playbook of `surface-playbooks.md`.

Already local: mandatory Reduced Motion in gpt-taste and minimalist, and named transition properties instead of `transition: all`. Not adopted: GSAP pin and scroll-distance recipes (library-specific code), brandkit intake and canvas rules (the brandkit entrypoint remains rejected), `install.sh`, `skill.sh` and the new shell test.

## Emil decision

Local `motion-quality.md` already required `transform`/`opacity`, no `transition: all`, sparing `will-change`, the inherited-CSS-variable trap and the CSS/WAAPI versus JS split. The Performance section now also carries:

- a 120Hz (about 8ms) frame budget, and no smoothness claim from a fast development machine;
- cause-first diagnosis, with `will-change` last;
- cheaper-property swaps, including `filter: drop-shadow()` for animated shadows;
- writing hand-rolled animation to element style or a motion value, not component state on every frame;
- CSS or WAAPI for motion that plays during navigation, fetching or hydration, with full `transform` strings instead of variable-backed motion-library shorthands;
- a small cap on animated `blur()`.

Not adopted: the initial-response ritual, and stopping after the report by default; local workflow and authority rules govern both. The 2026-10-06 `break-ui` range stays deferred. New coverage terms in `scripts/design_craft_emil_absorption.py` fail the check if this guidance is removed.

## Related Skill change

The same change set also tightens `motion-audit-planning.md` after the 2026-10-11 comparative loss on `emil-motion-planning-ablation` (design-craft 91, focused Emil 92):

- name the candidates set aside, with reasons;
- keep plans free of speculative experiments;
- show complete current and replacement blocks.

That rule change is local, not upstream absorption. It was written after the loss, so the re-collected comparative tranche is the test of whether it generalizes, not proof that it does.
