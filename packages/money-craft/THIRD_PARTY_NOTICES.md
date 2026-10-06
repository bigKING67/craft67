# Third-Party Notices

## AI Berkshire

Money Craft is a controlled derivative of AI Berkshire:

- Project: `xbtlin/ai-berkshire`
- Source: https://github.com/xbtlin/ai-berkshire
- Initial reviewed commit: `fef5533145e2a505c7e07592d61165c7485a98b9`
- License: MIT
- Copyright: `Copyright (c) 2026 xbtlin`

Money Craft adapts the upstream investment checklist, quality screen, company
research, earnings review, thesis tracking, financial-data discipline, exact
decimal calculations, and report-audit concepts. The pristine upstream source
is retained as a pinned Git submodule for review and is excluded from runtime
packages. File-level provenance is recorded in `sources.lock.json`.
The complete upstream MIT notice is retained in
`LICENSES/AI-BERKSHIRE-MIT.txt` and must remain in derivative distributions.

## Fuyao financial data documentation

Money Craft implements an independent REST client from the public API contract
at https://fuyao.aicubes.cn/docs. No Fuyao API data, credentials, or full
documentation snapshot is redistributed in the runtime package.

## yfinance

Money Craft optionally interoperates with `yfinance`:

- Project: https://github.com/ranaroussi/yfinance
- Package: https://pypi.org/project/yfinance/
- Locked adapter version: `1.7.0`
- License: Apache License 2.0

`yfinance` is not bundled into the core runtime; users install it and its
dependencies separately from `requirements-yfinance.txt`. The project states
that it is not affiliated with or endorsed by Yahoo, uses Yahoo's public APIs
for research and education, and that Yahoo Finance data is intended for
personal use. The library license does not grant redistribution rights to the
downloaded financial data. Money Craft therefore keeps adapter exports private
and treats official filings as the primary evidence source.

## FRED and ALFRED

Money Craft interoperates with the FRED® API and ALFRED® real-time/vintage
semantics documented by the Federal Reserve Bank of St. Louis:

- API documentation: https://fred.stlouisfed.org/docs/api/fred/
- Terms of Use: https://fred.stlouisfed.org/docs/api/terms_of_use.html

This product uses the FRED® API but is not endorsed or certified by the Federal
Reserve Bank of St. Louis.

FRED can expose series owned by third parties. API availability does not
override the data owners' copyright, attribution, use, or redistribution
restrictions. Money Craft keeps raw captures private, preserves each series'
source and notes, and does not represent the FRED or ALFRED names, marks, or
data as part of the Money Craft software license.
