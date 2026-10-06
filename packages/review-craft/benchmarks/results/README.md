# Runtime Benchmark Results

No release baseline is claimed yet. Run results outside the repository first, validate the
JSON, and only commit an immutable baseline from a clean source revision with the exact
environment and parameters recorded.

The default command runs the 1k-file tier. The 10k and 100k tiers are explicit because they
create and parse large temporary repositories:

```text
uv run --locked python scripts/benchmark_runtime.py run
uv run --locked python scripts/benchmark_runtime.py run --full
uv run --locked python scripts/benchmark_runtime.py validate --result <result.json>
```

Pull requests and direct pushes to `main` run a blocking 1k relative regression gate. The base
and candidate revisions execute serially on the same runner with three measured repetitions and
one warmup; any operation whose p50 wall time regresses by more than 20 percent fails the job.
The nightly 1k/10k and weekly 100k tiers remain non-blocking telemetry. The workflow uploads the
validated JSON and comparison receipt instead of committing mutable runner results here.

There is no immutable release baseline yet. The blocking gate compares the candidate with its
exact PR base or pre-push `main` revision; it is not a cross-runner historical performance claim.
If a release baseline is added later, bind its exact source, runner, Python, platform, parameters,
and content hash, compare repeated-run medians, and require an explicit baseline update rather
than silently accepting a slower run.

`pythonAllocatedPeakBytes` covers only in-process Python operations. Subprocess preflight
and validation memory is marked `NOT_CAPTURED_FOR_SUBPROCESS`; do not treat it as zero.
