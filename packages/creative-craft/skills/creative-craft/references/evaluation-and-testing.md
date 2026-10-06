# Evaluation and testing

Creative quality is multidimensional. An aggregate score is a comparison aid,
not an objective measure of taste.

## Independent dimensions

1. strategic fit;
2. audience relevance and truth;
3. proposition and message clarity;
4. concept distinctiveness;
5. hook and attention architecture;
6. narrative and emotional coherence;
7. visual, motion, copy, and sound craft;
8. production/provider feasibility;
9. reference fidelity and continuity;
10. channel and deliverable fit;
11. rights and provenance;
12. learning value and testability.

Score each dimension from 0 to 5 only when evidence exists.

## Gates

An aggregate score is blocked when any required gate fails:

- `rights_clear`;
- `brief_locked`;
- `deliverable_specified`;
- `actual_output_observed` when output quality is being judged.

A route-stage evaluation may set `actual_output_observed` to not applicable, but
must not score final rendering quality.

## Evidence coverage

Each dimension has:

- weight;
- score;
- evidence state;
- evidence note;
- confidence.

Coverage is the percentage of weight supported by evidence other than
`UNVERIFIED`.

By default:

- below 80% coverage: withhold aggregate score;
- 80–89%: score with low confidence;
- 90–99%: score with medium confidence;
- 100%: score with confidence determined by evidence quality, not coverage
  alone.

## Scoring

For covered dimensions:

```text
weighted_score =
  sum((score / 5) * weight) / sum(covered weights) * 100
```

Report:

- score;
- coverage;
- domain table;
- gates;
- confidence;
- unknowns;
- recommendation.

Do not compare scores produced from different briefs or materially different
evidence sets without normalization.

## Route evaluation versus output evaluation

### Route

Can score:

- strategy;
- audience relevance;
- proposition;
- distinctiveness;
- hook;
- narrative;
- brand fit;
- feasibility;
- channel fit;
- rights risk;
- testability.

Cannot score:

- actual rendering quality;
- text accuracy;
- motion stability;
- audio sync;
- final delivery integrity.

### Output

Can additionally score:

- observed visual craft;
- observed fidelity;
- observed motion and physics;
- observed audio;
- observed technical delivery.

## Testing

A useful test states:

- decision to be made;
- primary variable;
- control and treatment;
- audience and placement;
- metric;
- sample or time window;
- guardrail;
- stopping rule;
- interpretation boundary.

Examples of primary variables:

- opening hook;
- product reveal timing;
- headline;
- proof order;
- creator versus product protagonist;
- static versus motion;
- sound-on versus sound-light;
- direct demonstration versus metaphor.

Change one primary variable when attribution matters. A broad creative bake-off
may change multiple variables, but then the result selects a system rather than
explaining which component caused the difference.

## Learning

Promote a result into reusable guidance only when:

- the context and audience are recorded;
- the tested variable is known;
- the metric is relevant;
- alternative explanations are considered;
- the result repeats or has sufficient evidence;
- the learning is scoped, not universalized.
