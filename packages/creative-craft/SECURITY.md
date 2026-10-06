# Security and responsible use

Do not commit API keys, private source assets, confidential briefs, unreleased
campaigns, identity documents, or licensed media into this repository.

Creative Craft does not call image or video providers by default. When adding
an execution adapter:

- read credentials from environment variables or the host secret store;
- never log credentials or full private asset payloads;
- record only necessary generation receipts;
- keep source rights and likeness consent explicit;
- make network access and cost-bearing actions opt-in;
- preserve provider moderation and safety controls.

Report repository vulnerabilities privately to the maintainer. Provider abuse,
copyright, impersonation, or content-policy questions should be handled through
the relevant provider's official process.
