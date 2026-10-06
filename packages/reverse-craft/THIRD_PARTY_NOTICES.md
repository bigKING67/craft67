# Third-party notices

Reverse Craft contains original work plus selectively reused or reimplemented
mechanisms from the projects below. The machine-readable source map is
`skills/reverse-craft/references/provenance.json`.

## reverse-skill

- Source: <https://github.com/zhaoxuya520/reverse-skill>
- Reviewed commit: `37162cf9547c571c680c07005e9863d4610282dd`
- License: MIT
- Copyright: Copyright (c) 2026 zhaoxuya520
- Adapted from `skills/config/routing.json`, stored as
  `skills/reverse-craft/references/upstream/reverse-skill-routing.json`; Reverse Craft adds action-first bilingual IOC
  enrichment grammar and moves explicit R44 intent ahead of R9 malware analysis for mixed enrichment requests.
- Adapted: the 43-route taxonomy, deterministic scoring, specialist playbook organization, and bilingual routing
  regression concept. The local CTI/OSINT workflow is reimplemented for Reverse Craft's case/evidence contract.
- Adapted from the R0 decision-framework entry hook: Reverse Craft keeps R0 primary and records the current hypothesis,
  evidence gap, and decision delta before feasibility-gated replanning after bounded evidence-free progress. No ADF
  files or stage framework are copied.
- Not included: GPL-3.0 CTF Sandbox Orchestrator sources, AGPL Pentest Swarm
  sources, automatic bootstrap behavior, and forced action prompts.

MIT license text for the reused portion:

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

## codex-keysmith

- Source: <https://github.com/Jia-Ethan/codex-keysmith>
- Reviewed commit: `2cb7f382ea8a08e9af5a6d9c16580b45f639891a`
- License: MIT
- Copyright: Copyright (c) 2026 Jia-Ethan
- Reimplemented, not copied: dry-run-first setup, ownership manifests, atomic
  writes, transaction journal/recovery, prompt bank, scenario bank, and receipts.
- Not included: global Codex instruction deployment, hook isolation, GUI, or
  release product code.

## browser67

- Source: <https://github.com/bigKING67/browser67>
- Reviewed commit: `bb43570f139feafc2632f8da19f34b4863e6bccb`
- License: MIT
- Copyright: Copyright (c) 2026 bigKING67
- Runtime dependency only: browser67 is the canonical implementation of the
  `js-reverse` Skill and MCP runtime. Reverse Craft includes integration
  guidance and detection but no copied runtime/session implementation.
