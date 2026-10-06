# Money Craft

Money Craft is a portable Agent Skill for evidence-first global investment
research and wealth decision support: listed-company and industry research,
fund and portfolio analysis, earnings review, scenario valuation, and thesis
tracking. A-share support is one provider adapter, not the product boundary.
It is a controlled derivative of AI Berkshire and adds a consistent runtime
contract for Codex, Pi, Claude, and Grok.

## Daily-use baseline

Start with the [daily-use guide](docs/daily-use.md) and
[capability/evidence matrix](docs/capability-evidence-matrix.md). The
[2026-09-19 baseline receipt](acceptance/daily-use-baseline-20260919.json)
binds its historical Skill/install parity and bounded research evidence.
This is a working-tree use baseline, not a release or investment-performance claim.

The subsequent [Amazon thesis lifecycle check](docs/amazon-thesis-lifecycle-20260919.md)
preserves real tracking revisions and the first full-host timeout. The subsequent
[company-research closeout](docs/amazon-company-research-closeout-20260919.md)
verifies the installed patch, research sealing, and the full natural-language question
on the same frozen Skill. Investment valuation remains unverified.

## Runtime boundaries

- Canonical skill: `skills/money-craft/`
- Runtime: Python 3.10+, standard library only
- Structured data: optional Fuyao A-share REST, persistent isolated `yfinance` Hong Kong/U.S. secondary-market, and FRED/ALFRED macro/vintage adapters
- Research output: `~/Documents/sixseven/money` by default, overridable with `MONEY_CRAFT_OUTPUT_ROOT`
- Without a market adapter: use the target regulator, exchange, issuer/fund
  filings, and other official sources; never invent missing figures
- No automatic trading, order placement, account access, or full-market dumps

The core research runtime remains standard-library-only. The optional final
report renderer uses Markdown, WeasyPrint, and pypdf from a dedicated local
environment and produces implementation-neutral `report.html` / `report.pdf`
reading artifacts.

Money Craft separates configuration, persistent runtime data, and cache using
the XDG base-directory contract:

| Category | Default | App-specific override |
|---|---|---|
| Credentials and user configuration | `~/.config/money-craft` | `MONEY_CRAFT_CONFIG_HOME` |
| Optional venvs and persistent runtime data | `~/.local/share/money-craft` | `MONEY_CRAFT_DATA_HOME` |
| Rebuildable cache | `~/.cache/money-craft` | `MONEY_CRAFT_CACHE_HOME` |

`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, and `XDG_CACHE_HOME` are honored when the
app-specific variables are absent. All overrides must be absolute paths. For
source-repository development only, copy `.env.example` to the ignored
`.env.local`, set mode `0600`, and explicitly select it with an absolute
`MONEY_CRAFT_ENV_FILE`; installed Skills never search the current directory or
parent folders for dotenv files. Existing process variables take precedence.

The Fuyao API key must be supplied through the process environment or the protected
local file below. Do not pass it on the command line, put it in a repository
file, or include it in a report.

```bash
install -d -m 700 ~/.config/money-craft
# Write the key without putting it in shell history, then restrict it to the current user.
read -rs 'FUYAO_API_KEY?Fuyao API key: '; printf '%s\n' "$FUYAO_API_KEY" > ~/.config/money-craft/fuyao-api-key; unset FUYAO_API_KEY
chmod 600 ~/.config/money-craft/fuyao-api-key
python3 skills/money-craft/scripts/money_craft.py doctor --json
python3 skills/money-craft/scripts/money_craft.py data search --query 贵州茅台
```

See `skills/money-craft/references/providers/fuyao.md` for the bounded Fuyao
operations and evidence-capture contract.

For Hong Kong and U.S. research, install the pinned optional adapter in a
dedicated environment instead of changing the system Python:

```bash
MONEY_CRAFT_DATA_HOME="${MONEY_CRAFT_DATA_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/money-craft}"
python3 -m venv "$MONEY_CRAFT_DATA_HOME/venvs/data"
"$MONEY_CRAFT_DATA_HOME/venvs/data/bin/python" -m pip install \
  -r skills/money-craft/requirements-yfinance.txt
"$MONEY_CRAFT_DATA_HOME/venvs/data/bin/python" \
  skills/money-craft/scripts/money_craft.py doctor --json
```

After this environment exists, launching `money_craft.py` with the system
`python3` transparently re-executes the same command with the persistent data
runtime. An already active report or other explicit venv is not replaced.
`MONEY_CRAFT_DATA_PYTHON` may select another controlled interpreter.

`yfinance` and Yahoo Finance data are secondary, personal-use research inputs;
official regulator, exchange, and issuer filings remain primary. See
`skills/money-craft/references/providers/yfinance.md` for symbol mapping,
supported operations, capture semantics, and data-use boundaries.

FRED and ALFRED supply macroeconomic series and historical data vintages. FRED
answers what the latest revised history shows; an ALFRED `as-known-on` query
answers what was available to a decision maker on a past date. This distinction
prevents revised GDP, inflation, and employment data from leaking future
information into historical research or backtests.

Every FRED request needs its own API key. If a key has appeared in chat, a
screenshot, a log, or shell history, revoke it in FRED Account and create a new
one before saving it. Enter the replacement without echoing it:

```bash
install -d -m 700 ~/.config/money-craft
read -rs 'FRED_API_KEY?FRED API key: '; printf '%s\n' "$FRED_API_KEY" > ~/.config/money-craft/fred-api-key; unset FRED_API_KEY
chmod 600 ~/.config/money-craft/fred-api-key
python3 skills/money-craft/scripts/money_craft.py doctor --json
python3 skills/money-craft/scripts/money_craft.py data search \
  --provider fred --query "10-year breakeven inflation" --limit 10
python3 skills/money-craft/scripts/money_craft.py data observations \
  --series-id T10YIE --start 2020-01-01 --end 2026-09-01
python3 skills/money-craft/scripts/money_craft.py data observations \
  --series-id GDPC1 --start 2019-01-01 --end 2024-12-31 \
  --as-known-on 2024-12-31
```

This product uses the FRED® API but is not endorsed or certified by the Federal
Reserve Bank of St. Louis. FRED can include third-party series with separate
rights; access through the API does not grant redistribution permission. See
`skills/money-craft/references/providers/fred.md` for the bounded operations,
macro-series map, vintage semantics, key handling, and evidence contract.

## Final report rendering

Money Craft renders audited Markdown into a responsive, offline HTML report and
an A4 PDF using the `editorial-ivory` research-publication design system. The canonical Markdown,
source manifest, audit, and offline verifier remain the research truth; the
HTML/PDF are hash-bound reading renditions and cannot change the conclusion or
evidence.

Create the dedicated optional runtime once:

```bash
MONEY_CRAFT_DATA_HOME="${MONEY_CRAFT_DATA_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/money-craft}"
python3 -m venv "$MONEY_CRAFT_DATA_HOME/venvs/report"
"$MONEY_CRAFT_DATA_HOME/venvs/report/bin/python" -m pip install \
  -r skills/money-craft/requirements-report.txt
```

Render only to an explicit repo-external preview or rendition directory:

```bash
"${MONEY_CRAFT_REPORT_PYTHON:-${MONEY_CRAFT_DATA_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/money-craft}/venvs/report/bin/python}" \
  skills/money-craft/scripts/money_craft.py report render \
  --source <revision>/report.md \
  --output-dir /tmp/money-craft-report-preview \
  --evidence-manifest <revision>/sources/sources.manifest.json \
  --audit <revision>/report.audit.json \
  --revision-manifest <revision>/REVISION.json \
  --archive-manifest <revision>/manifest.json --json

"${MONEY_CRAFT_REPORT_PYTHON:-${MONEY_CRAFT_DATA_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/money-craft}/venvs/report/bin/python}" \
  skills/money-craft/scripts/money_craft.py report verify \
  --source <revision>/report.md \
  --html /tmp/money-craft-report-preview/report.html \
  --pdf /tmp/money-craft-report-preview/report.pdf --json
```

The renderer embeds CSS, JavaScript, and deterministic inline SVG charts into a
single portable HTML file. Source URLs remain visible as non-navigable locators,
so opening an archived report never fetches remote assets. Direct rendering
never defaults to the canonical revision directory. See
`skills/money-craft/references/report-rendering.md` for the visual, archive, and
verification contract.

## Research and thesis workflow

After resolving the exact global security identity and latest formal reporting
period, generate a model-free company research contract. Non-A-share research
uses Money Craft's open `MARKET:SYMBOL` identity, explicit base currency, fiscal
period end, and latest annual period:

```bash
python3 skills/money-craft/scripts/money_craft.py research plan \
  --security <issuer-name> --security-id <MARKET:SYMBOL> \
  --base-currency <three-letter-currency> \
  --as-of <YYYY-MM-DD> --latest-report <YYYY-1..4> \
  --latest-report-end <YYYY-MM-DD> --latest-annual-report <YYYY-4> \
  --provider auto --provider-mode auto --json
```

A-share callers remain backward compatible: `--thscode 000333.SZ` derives
`CN-SZ:000333` and defaults the base currency to CNY. Calendar-quarter A-share
plans may omit `--latest-report-end`.

The plan binds the identity, dates, mandatory and conditional official-evidence
requirements, a bounded market-appropriate Provider operation matrix, financial-reconciliation
contract, expected artifacts, and audit gates. It does not access the network,
create a report, or claim that any stage has completed.

Create a resumable local research run from that same plan contract:

```bash
python3 skills/money-craft/scripts/money_craft.py research init \
  --security <issuer-name> --security-id <MARKET:SYMBOL> \
  --base-currency <three-letter-currency> \
  --as-of <YYYY-MM-DD> --latest-report <YYYY-1..4> \
  --latest-report-end <YYYY-MM-DD> --latest-annual-report <YYYY-4> \
  --provider auto --provider-mode auto --json

# Run only when plan.json contains executable provider_operations.
python3 skills/money-craft/scripts/money_craft.py research collect \
  --workspace <workspace-returned-by-init> --resume --json
```

Without `--workspace`, `init` creates a unique private run under the Money
archive without pretending that the run is a sealed report:

```text
~/Documents/sixseven/money/
└── <identity>-<company>/
    └── <YYYY-MM-DD>/
        ├── .research/<run-id>/       # mutable Money Craft research run
        │   ├── plan.json
        │   ├── case.json
        │   ├── run-state.json
        │   ├── evidence/
        │   ├── financial-reconciliation.json
        │   ├── report.md
        │   └── thesis.md
        ├── .working/<investment-run-id>/  # formal archive staging, managed separately
        └── revisions/rNNNN/               # immutable, audit-gated final archive
```

The command-line `--output-root` takes precedence over
`MONEY_CRAFT_OUTPUT_ROOT`, which takes precedence over the default path.
`--workspace` remains available for an explicitly managed private directory.
The dynamic workspace printed by `init` is the only path that subsequent run
commands should use.

`init` is model-free and offline. It writes an immutable `plan.json`, derives
`case.json` from that plan instead of maintaining a second operation matrix,
creates draft report/thesis files, and starts an append-only `run-state.json`.
`collect` is the explicit selected-Provider network boundary: it executes only
the bounded operations in the derived case, writes private non-overwriting
captures, and returns non-zero when a provider gap remains. Auto routing selects
Fuyao for A shares and the optional yfinance adapter for Hong Kong and U.S.
equities. For an unsupported market, an unconfigured adapter, or
`provider-mode=disabled`, the plan contains no executable operations; skip
`collect`, import official evidence, and preserve the declared provider gap.

Official filings remain an explicit local import rather than a provider
substitute or an automatic download:

```bash
python3 skills/money-craft/scripts/money_craft.py research import-official \
  --workspace <workspace-returned-by-init> \
  --source-id S11 --file /path/to/formal-report.pdf \
  --url https://official.example/formal-report.pdf --json

python3 skills/money-craft/scripts/money_craft.py research status \
  --workspace <workspace-returned-by-init> --json

python3 skills/money-craft/scripts/money_craft.py research finalize \
  --workspace <workspace-returned-by-init> --json
```

`S11/S12/S13` are mandatory. `S18`, `S19`, and `S20` are conditional slots for
material transaction or capital-structure disclosures, official management
Q&A, and post-reporting-period material events. They do not block a run when
irrelevant, but must be imported when the corresponding fact affects the
research conclusion. Each route must also be resolved as `not-triggered` or
`imported` in `financial-reconciliation.json`; a mismatch with the captured
evidence fails finalization.

Before finalization, complete and audit the generated reconciliation artifact:

```bash
python3 skills/money-craft/scripts/money_craft.py audit reconciliation \
  <workspace-returned-by-init>/financial-reconciliation.json --json
```

The import copies a bounded PDF or HTML snapshot, records its HTTPS source,
and binds its SHA-256 without retaining the input path. `status` is offline and
recomputes provider, official-source, reconciliation, report, thesis, manifest,
audit, and receipt state from the workspace. `finalize` requires terminal
evidence, builds a metadata-only manifest, runs all four report/thesis audits
plus the reconciliation audit, and writes an immutable completion receipt only
when every audit passes. Provider gaps
remain explicit limitations; none of these commands access an account or place
a trade. Explicit repository-local workspaces must stay under the ignored
`local/research/` tree. The archive `.research/` run is private working state,
not a formal archive revision;
promotion to `.working/<investment-run-id>` and `revisions/rNNNN` remains under
the separate investment archive ledger, verifier, and seal gates.

For a repeatable thesis revision, prepare the update contract from an already
audited thesis and compare the completed revision afterward:

```bash
python3 skills/money-craft/scripts/money_craft.py thesis prepare-update \
  --previous thesis-old.md --as-of 2026-11-01 --json

python3 skills/money-craft/scripts/money_craft.py thesis diff \
  --previous thesis-old.md --current thesis-new.md --json
```

The diff fails closed on identity changes, time reversal, rewritten update
history, missing current update rows, or an invalid report/financial audit. Its
signal is a review priority, never an order or trading instruction.

### Earnings-to-thesis update

Compare source-bound adjacent fiscal periods, review dated expectations when
available, reconcile three earnings-multiple valuation bridges, and prepare a
hash-bound thesis proposal:

```bash
python3 skills/money-craft/scripts/money_craft.py earnings review \
  --input <earnings-update-input.json> --previous-thesis <audited-thesis.md> --json
```

See the [input and review contract](skills/money-craft/references/earnings-review.md)
and the [two-filing historical acceptance case](acceptance/earnings/README.md).
The proposal requires review before entering the existing tracking workflow;
positive financial changes do not automatically establish thesis support.

### Company-level tracking archive

Persist an audited thesis update next to the company's dated research folders:

```text
~/Documents/sixseven/money/
└── <identity>-<company>/
    ├── <YYYY-MM-DD>/revisions/rNNNN/  # immutable formal research archive
    └── tracking/
        ├── current.json               # atomic pointer to the latest tracking revision
        ├── .working/<run-id>/         # private editable update workspace
        └── revisions/tNNNN/           # read-only thesis/card/state/diff/audits/hashes
```

Create the first tracking workspace from an audited thesis, complete the three
editable files using new evidence, then seal the result:

```bash
python3 skills/money-craft/scripts/money_craft.py track init \
  --tracking-root <company-dir>/tracking \
  --previous <audited-thesis.md> \
  --source-revision <formal-revision-dir> \
  --as-of 2026-11-01 --json

python3 skills/money-craft/scripts/money_craft.py track check \
  --workspace <workspace-returned-by-init> --json

python3 skills/money-craft/scripts/money_craft.py track status \
  --tracking-root <company-dir>/tracking --json
python3 skills/money-craft/scripts/money_craft.py track verify \
  --tracking-root <company-dir>/tracking --json
```

Later `track init` calls resolve the previous thesis from `current.json`, so
`--previous` is only required for the first revision. All four commands are
offline and model-free. `track check` validates the append-only thesis diff,
both audits, state-to-thesis hypothesis/red-line parity, deterministic health
score, unresolved placeholders, checksums, and the no-trading boundary before
creating a read-only `tNNNN` and atomically advancing `current.json`. It does
not fetch evidence or write research conclusions. See
`skills/money-craft/references/tracking-workflow.md` for the complete contract
and escalation rules.

## Public data boundary

The repository distributes code, schemas, synthetic test fixtures, derived
research reports, audits, and hash-bound evidence manifests. It does not
distribute Fuyao response payloads, yfinance adapter exports, capture receipts, downloaded filings, or
web-page snapshots. Keep that material under the ignored
`local/evidence/<case-id>/` tree.

The Golden Cases in `artifacts/acceptance/600519/` and
`artifacts/acceptance/000333/` demonstrate this split across Shanghai and
Shenzhen listings. Each `evidence-manifest.json` records source metadata and
SHA-256 digests, while the corresponding private files remain local. Verify a
public manifest alone, or additionally verify its local evidence when available:

```bash
python3 scripts/verify_evidence.py artifacts/acceptance/600519/evidence-manifest.json --metadata-only
python3 scripts/verify_evidence.py artifacts/acceptance/600519/evidence-manifest.json --require-private
```

Acceptance cases are declared under `acceptance/cases/`. The collector only
supports the bounded Money Craft REST operations; it does not accept arbitrary
URLs or headers, and credentials never appear in a case file or command line.
Collection is non-overwriting by default and can resume an interrupted case:

```bash
python3 scripts/acceptance_case.py collect --case acceptance/cases/000333.json
python3 scripts/acceptance_case.py collect --case acceptance/cases/000333.json --resume
python3 scripts/acceptance_case.py build-manifest --case acceptance/cases/000333.json
python3 scripts/acceptance_case.py verify --case acceptance/cases/000333.json --require-private
```

Official filings listed by a case must be acquired separately from the declared
HTTPS source and placed under its private evidence root before building the
public manifest. This keeps issuer/filing review explicit instead of turning a
structured-data response into a substitute for primary disclosure.

Fixtures under `tests/fixtures/fuyao/` are synthetic contract examples, not
captured market data.

## Host discovery

Codex, Pi, and Grok discover the shared Agent Skills user root. Install the
canonical copy there:

```bash
python3 scripts/install_skill.py --host agents
```

Claude Code 2.1.x discovers personal standalone Skills from
`~/.claude/skills/`, not `~/.agents/skills/`. Install its compatibility copy
separately:

```bash
python3 scripts/install_skill.py --host claude
```

Use `--force` only after reviewing an existing installation; the installer
creates a timestamped backup before replacement. `--target-root` supports an
isolated acceptance test. Every installation is a symlink-free atomic copy with
`INSTALL_PROVENANCE.json`; credentials are never copied into a Skill directory.

## Validation

For bounded test environments, automatic dependency cleanup, a read-only
storage inventory, and copy-on-write deduplication of identical evidence
(`money_craft.py storage dedupe`), see [local test storage management](docs/test-storage.md).

```bash
npm test
npm run validate
npm run package-check
npm run host-smoke
# Optional report runtime only:
"${MONEY_CRAFT_REPORT_PYTHON:-${MONEY_CRAFT_DATA_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/money-craft}/venvs/report/bin/python}" \
  scripts/report_smoke.py
```

The default host smoke is model-free. It first verifies the shared Agent Skills
installation against the canonical tree hash and runs the installed runtime
self-test. Codex is then checked through its model-visible prompt catalog, Pi
through a fresh offline RPC `get_commands`, and Grok through `inspect --json`.
Claude Code is checked through its separate compatibility installation hash and
installed runtime self-test because 2.1.x exposes no model-free personal Skill
discovery command. Therefore `fresh_session_tested` remains false and the Claude
result is explicitly partial; no host model is invoked and no model usage is
incurred. `npm run host-smoke:static` keeps the manifest-only check.

`scripts/report_smoke.py` requires the optional dependencies from
`skills/money-craft/requirements-report.txt`. It renders the tracked 600519
acceptance report to a temporary directory and verifies the portable HTML and
PDF before deleting the temporary rendition. CI runs this as a dedicated report
job so the core standard-library matrix remains independent of report packages.

These gates validate source, package, and local discovery behavior. Fuyao, yfinance, and FRED live
access and paid fresh-session host behavior remain separate evidence layers and
must not be claimed from static or model-free validation alone.

## Upstream updates

Money Craft will serve both a Skill and an application, starting with the Skill
and a shared research core. See the [upstream strategy and maintenance workflow](docs/upstream-strategy.md)
and the [155-page MyInvestPilot documentation review](docs/upstreams/myinvestpilot.md).
References are evaluated per capability; they are not automatically installed dependencies.

```bash
python3 scripts/upstream_status.py --all --json
python3 scripts/upstream_status.py --all --fetch --json
python3 scripts/upstream_status.py --source myinvestpilot --snapshot /tmp/myinvestpilot-capture.json --json
```

The multi-source interface returns v2 results: cached records, pending reviews,
fresh observations and unavailable sources stay distinct. MyInvestPilot requires
a complete browser catalog capture; the CLI does not mistake partial server HTML
for a full directory. Exit 2 means cached/stale/pending review, exit 1 means an
input or observation failure, and exit 0 means every selected source is current.
Neither checking nor snapshot conversion advances review/adoption records.

AI Berkshire is pinned under `upstreams/ai-berkshire`. Run:

```bash
python3 scripts/upstream_status.py --fetch --json
```

The command is read-only with respect to Money Craft source. Review each change
and update `sources.lock.json` only when it is intentionally absorbed, deferred,
or classified as irrelevant. Every review range uses a fixed `through_commit`.
Report-only ranges account for excluded content; selective ranges separately
record reviewed source, accounted exclusions, reimplemented mechanisms, and
non-absorbed decisions. Advancing the review baseline never moves the submodule
pin or pretends generated packages, reports, or account records were absorbed.
Never auto-merge upstream changes into the canonical skill.

财报前瞻可先用 `earnings seal-preview` 保存独立基线，再用 `earnings replay-preview` 对照实际结果和催化剂证据。预期按分析师/管理层/一致预期分别保存，历史重建明确标注，逾期事件不会自动视为兑现；详见 [财报研究合同](skills/money-craft/references/earnings-review.md)。

当前建设优先级：先完善 Skill 与共用研究核心，完成证据、计算、封存和跨模块流程的集中审查、整改及端到端验收。应用建设是核心能力成熟后的独立后续阶段，不因一批测试通过而自动启动。`scripts/earnings_smoke.py <CLI路径>` 可离线验证源码或临时安装包的财报链，使用明确标记的合成数据，不提供投资效果证明。
