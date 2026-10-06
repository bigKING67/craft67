# Systems, cloud, attack chains, and application security

Model identities, trust zones, reachable services, data/control planes, credentials/tokens (redacted), and state changes.
Every multi-step chain needs a precondition and evidence per edge; a tool alert is not a chain.

## R10 - Attack chain

- Define objective and rules of engagement; create an asset/identity/trust graph before expanding reconnaissance.
- Validate one edge at a time: access -> capability -> next trust boundary. Record cleanup and stop conditions.
- Prefer the quietest sufficient technique and reuse established evidence; do not rescan blindly between modules.
- A path is complete only when every edge is observed or clearly marked hypothetical.

## R11 - Pentest tools

- Select nmap/nuclei/ffuf/sqlmap/Burp/etc. only after defining target, hypothesis, rate, timeout, and expected evidence.
- Start passive or narrow; constrain concurrency and payload space. Save exact versions/templates/options and bounded output.
- Manually reproduce high-impact scanner results. Treat negative scan output as coverage-limited, not proof of absence.

## R13 - Supply chain

- Map source -> dependency resolution -> build runner -> artifact -> registry -> deploy; pin lockfiles, images, and attestations.
- Generate SBOM and reachability context; separate vulnerable version presence from reachable exploitability.
- Inspect CI permissions/secrets exposure, provenance/signing, cache poisoning, dependency confusion, and update policy.
- Hash artifacts and verify source/build/release identity rather than trusting labels.

## R23 - Cloud/Kubernetes

- Inventory account/project/tenant, identity, region, network, control plane, workloads, RBAC/IAM, secrets, storage, and logs.
- Prefer read-only API/config evidence. Query metadata only from an explicitly scoped fixture/workload.
- In Kubernetes, trace service account -> RBAC verb/resource -> admission/runtime -> node/cloud identity.
- Distinguish manifest intent, live object state, and effective cloud permission.

## R24 - Windows/Active Directory

- Map forests/domains/trusts, hosts, users/groups, sessions, Kerberos, AD CS, delegation, shares, and endpoint controls.
- Preserve ticket/token fields and timestamps without storing reusable credentials. Validate BloodHound-style edges directly.
- Separate directory privilege, local admin, token/session availability, and actual execution path.
- Use controlled accounts and reversible changes; record cleanup of tickets, services, tasks, and certificates.

## R26 - Code audit/SAST

- Map entrypoints, frameworks, auth/session, untrusted sources, validation, dangerous sinks, storage, async jobs, and egress.
- Trace source-to-sink and the enforcing boundary. Confirm configuration/runtime reachability before severity.
- Use Semgrep/CodeQL as candidate generators; add a minimal regression test for verified findings and fixes.
- Report file/line plus execution path and invariant, not pattern matches alone.

