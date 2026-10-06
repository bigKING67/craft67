# Web, API, automation, database, and identity

Capture request order, redirects, storage, cookies/tokens (redacted in reports), frames/workers, client bundles,
API schemas, server responses, and the exact identity/session boundary. Do not infer server authorization from UI code.

## R3 - JavaScript/frontend reverse

- Read `../browser67-js.md`; browser67 `js-reverse` is the canonical live runtime.
- Start from the decisive request/parameter and initiator. Trace plaintext -> transform -> key/material -> serialization.
- Hook before trigger, collect one bounded sample, then export a rebuild bundle/local harness.
- Validate local output against captured pairs and a safe replay/fixture. Source resemblance alone is insufficient.

## R12 - API security

- Build an endpoint/object/action/auth matrix from observed traffic and schemas; include tenant/user/object ownership.
- Change one identifier/claim/method/content type at a time using separate authorized identities where required.
- Cover object/function/property authorization, authentication/session, mass assignment, rate/resource limits, and errors.
- Record exact request/response pairs with secrets redacted and server state reset/cleanup.

## R19 - Browser/desktop automation

- Automation is a means, not evidence by itself. Pin the window/tab/page and verify visible state after each mutation.
- Use browser67 for logged-in browser state, managed tabs, downloads/uploads, and lifecycle; use desktop UI control only
  when a purpose-built API is unavailable.
- Make selectors semantic and waits state-based. Preserve receipts/screenshots for decisive visible effects.
- Never adopt or close unrelated user tabs/windows without explicit authorization.

## R35 - Database security

- Identify engine/version/listeners/auth/TLS, roles, grants, schemas, extensions/plugins, backups, replicas, and audit settings.
- Use parameterized, read-only queries first. Validate injection through an application boundary without destructive payloads.
- Distinguish exposed service, authenticated privilege, query execution, filesystem/OS reach, and data impact.
- Snapshot/backup before any authorized mutation and record rollback.

## R37 - SAML/OIDC federation

- Diagram browser, relying party/client, IdP/authorization server, token endpoint, keys/JWKS, and session issuance.
- Capture request IDs, state/nonce/PKCE, redirect URI, audience/issuer, signature/encryption, timestamps, and key selection.
- Test parser/validation consistency and account linking with controlled identities; never replay unrelated real-user assertions.
- Separate token acceptance from authorization and from session persistence. Redact assertions/tokens in artifacts.

