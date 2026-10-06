## ADDED Requirements

### Requirement: Reproducible financial comparison
The core SHALL compare declared metrics only after binding source files, locators, dates, securities, currencies and comparable fiscal windows. Unverified comparison bases SHALL block downstream calculations and tracking proposals.

#### Scenario: Prior actuals were restated
- **WHEN** a same-period restated comparator and reason are supplied
- **THEN** the comparison uses the restated values while the frozen prior valuation retains its original inputs and both adjustments are visible

#### Scenario: Evidence is invalid
- **WHEN** a file hash, unit, fiscal window or source availability date is incompatible
- **THEN** review fails without updating a thesis or producing a success receipt

### Requirement: Dated expectations
Actual-versus-expected comparisons SHALL require a period-matched, source-bound expectation available before the actual-result disclosure.

#### Scenario: No dated expectation exists
- **WHEN** no expectation is supplied
- **THEN** the update reports its absence and makes no beat/miss claim

### Requirement: Conserved scenario bridge
Positive-earnings multiple models SHALL produce bear/base/bull endpoints, explicit old/new assumptions and ordered contributions for earnings, earnings factor, multiple, shares and FX. Contributions plus declared rounding residual SHALL reconcile to the endpoint difference.

#### Scenario: Earnings and multiples both change
- **WHEN** actual earnings and model assumptions change
- **THEN** each contribution is recomputed in a documented order, assumptions remain HYPOTHESIZED and values are not represented as market price targets

### Requirement: Reviewed tracking handoff
The update SHALL bind the prior audited thesis hash and cover all existing hypothesis/red-line IDs with proposed statuses, rationales and source locators. It SHALL NOT silently alter prior history or promote numeric changes into thesis support.

#### Scenario: A proposed update is accepted for tracking
- **WHEN** a researcher reviews the proposal and creates a candidate using the existing tracking workflow
- **THEN** append-only history, report/financial audits, state mapping and sealed-revision verification remain required
