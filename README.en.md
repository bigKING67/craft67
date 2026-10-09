English · [简体中文](README.md)

# craft67

The source repository for Craft projects and Agent Skills. Design, creative work, engineering review, investment research, commerce operations, browser automation, and more are maintained in one place, and each package keeps its own version, dependencies, tests, and license. It currently contains 10 projects and 18 Skills; for the exact entry points and check commands, [catalog.json](catalog.json) is the source of truth.

## Choose a capability

| Project and usage guide | Purpose and output | Skill |
| --- | --- | --- |
| [Design Craft](packages/design-craft/README.md) | Design, implementation, and visual verification for web, desktop, and native interfaces | design-craft |
| [Creative Craft](packages/creative-craft/README.md) | Ad concepts, copywriting, art direction, image briefs, and video plans | creative-craft |
| [Review Craft](packages/review-craft/README.md) | Engineering review with defined coverage and evidence, plus remediation and acceptance | review-craft |
| [Money Craft](packages/money-craft/README.md) | Investment research, financial reports, valuation, and portfolio analysis | money-craft |
| [Whoami](packages/whoami/README.md) | BaZi and Zi Wei Dou Shu chart calculation, with evidence-based interpretation | whoami |
| [Browser67](packages/browser67/README.md) | Real-browser operation and authorized front-end JS reverse engineering; includes a CLI, an MCP server, and an extension | browser67, js-reverse |
| [Commerce Growth OS](packages/commerce-growth-os/README.md) | Business strategy, marketing, platform operations, and business analytics | 4 commerce Skills, 4 marketing Skills |
| [3D Craft](packages/3d-craft/README.md) | Building and verifying Blender product props, GLB files, and Web3D viewers | 3d-craft |
| [Reverse Craft](packages/reverse-craft/README.md) | Authorized reverse engineering, CTF, DFIR, protocol, and threat-evidence analysis | reverse-craft |
| [Write Craft](packages/write-craft/README.md) | Turns complex plans, progress, and engineering explanations into documents readers can evaluate and act on, and reviews and rewrites project READMEs | write-craft |

## Use a Skill

1. Pick a capability from the table above, read that package's README, and install or build it as described there.
2. Enable the Skill in your host. Skills load on demand, so you do not need to install everything at once.
3. After the source changes, sync with the relevant installer and verify the load in a new session. Matching files do not mean the running session has loaded the new version.

Get the maintained source:

```sh
git clone https://github.com/bigKING67/craft67.git
cd craft67
```

Installation differs by package. Design / Creative / Money / 3D use their existing installers and target-directory arguments. Commerce must be built or installed through the package's `scripts/install.sh`, which assembles the shared contracts the eight independent bundles need. Whoami requires installing dependencies and building first; for standalone distribution, run `npm run pack:skill -- <non-existent target directory>`. Browser67's Skill and its CLI/MCP/extension are installed separately. Review / Reverse / Write keep using the distribution entry points inside their packages.

`packages/` is the maintained source; directories such as `~/.agents/skills` hold host-installed copies. The 10 old GitHub repositories have been deleted, so historical download links are not valid install sources. For new releases, the actual state of the relevant package in [craft67 Releases](https://github.com/bigKING67/craft67/releases) is authoritative.

## Development and verification

Day-to-day development happens inside `packages/<name>/`; Git operations belong to the craft67 root repository. Before making changes, read `AGENTS.md` at the root and inside the package.

The root checker requires Python 3.12+ and Git. The unified CI for JavaScript packages uses Node 24; Whoami's pinned acceptance evidence is tied to **Node 24.18.0**. Review Craft also needs uv; other dependencies and platform requirements are in each package's README. The checker does not install dependencies for you.

```sh
# Show versions, check commands, and the current directory/registration relationships
python3 scripts/versions.py
python3 scripts/check.py --list
python3 scripts/verify-layout.py

# Root metadata and checker regression tests
python3 scripts/versions.py --check
python3 -m unittest discover -s scripts -p 'test_*.py'

# Example: prepare Whoami's dependencies, then run its gate
cd packages/whoami
npm ci --ignore-scripts
cd ../..
python3 scripts/check.py --package whoami
```

To check several affected packages, pass `--package` repeatedly. Without it, all packages are checked, and the dependencies of every package must be prepared first. The check commands do not install anything globally, commit, or publish.

To get upstream reference content or verify the actual submodule checkouts:

```sh
git submodule update --init --recursive
python3 scripts/verify-layout.py --check-checkouts
```

The default structure check compares the catalog, directories, the root `.gitmodules`, and the pins in the current Git index. It does not treat uninitialized checkouts as verified. The historical migration audit is kept separately in `scripts/verify-migration.py` and is not part of the day-to-day development gate.

## CI and versions

The [root unified workflow](.github/workflows/check.yml) first verifies structure and version metadata, then generates the check matrix for all packages from the catalog; a new run on the same event and branch cancels any older run still in progress. Browser67 also has a manually triggered [multi-platform and isolated-browser check](.github/workflows/browser67-platform.yml). Design's [native evidence](.github/workflows/native-runtime.yml), [performance collection / candidate verification](.github/workflows/benchmark.yml), and [certification entry](.github/workflows/release-certify.yml) are likewise manually triggered; the existence of an entry point does not mean certification has passed, and the prerequisites are described in the release migration document. Results are on [Actions](https://github.com/bigKING67/craft67/actions/workflows/check.yml). The `.github/` directories inside packages keep the original engineering contracts and release references; GitHub does not run them automatically as root workflows.

Each package is versioned independently, with tags in the form `<package>/v<version>`; a snapshot of craft67 as a whole is identified by its commit SHA. For version sources, mirror sync, and release constraints, see [Versioning and releases](docs/versioning.md). Source version, passing CI, an official Release, installed files, and the host's runtime state are distinct states; offline CI does not replace real-browser, target-platform, or formal installation acceptance. Not all of the original release workflows have been moved to this repository yet; for the candidate-build entry points and the per-package gaps, see [Release process migration](docs/release-migration.md).

## Migration record and license

This repository was created by importing source snapshots and does not include the full history of the old repositories. For source commits and an import summary, see [migration-sources.json](docs/migration-sources.json); for stage-by-stage acceptance, see the [migration history](docs/migration.md); for what happens next to the old directories and old remotes, see the [retirement record](docs/remote-retirement.md). Stage statuses in the historical records do not represent the current installation or release state.

The root repository does not relicense the packages; licenses and third-party notices stay at their original paths. Credentials, local execution configuration, personal data, dependency directories, caches, and run output are not part of the public source.
