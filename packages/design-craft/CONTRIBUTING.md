# Contributing

## Scope and directories

- `skills/design-craft/` is the only published runtime product.
- `tools/design_craft/` contains repository governance, validation,
  benchmarking, installation migration, evidence, and release tooling.
- `contracts/` contains machine-readable policy and schema truth.
- `tests/` contains unit, contract, integration, and adversarial coverage.
- `benchmarks/` contains benchmark documentation and controlled baselines.
- `evals/` contains specs, fixtures, current evidence, and immutable history.
- `upstreams/` is pristine provenance and must not become runtime authority.

Do not add repository governance to the skill runtime, duplicate runtime
wrappers under `scripts/`, or use Markdown tables as machine databases.

## Local validation

Run targeted tests first, then expand:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 make lint
PYTHONDONTWRITEBYTECODE=1 make contract-tests
PYTHONDONTWRITEBYTECODE=1 make validate-portable
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.design_craft benchmark --scale smoke
```

Changes to the canonical skill invalidate source-bound comparative,
cross-agent, and native evidence. Do not edit hashes or recorded commits to
make old evidence appear current; archive it and recapture against the final
release-candidate commit.

## Pull requests

Keep changes responsibility-scoped. Report the affected contracts, exact
validation commands, generated artifacts, remaining unverified hosts/devices,
and performance comparison when a hot path changes. A source completeness
score is not a product-quality or release-certification claim.

Pull requests are recommended for external contributions and risky changes,
but they are not required for maintainer-owned, locally verified work. A
maintainer may use the direct path:

```bash
git add -- <scoped-paths>
git commit -m "<type>(<scope>): <summary>"
git push origin main
```

Run targeted local validation before pushing. GitHub CI remains post-push
evidence and should be investigated when it fails, but normal fast-forward
pushes do not wait for remote status checks. Main and release tags still reject
deletion and non-fast-forward updates.
