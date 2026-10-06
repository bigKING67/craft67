# Contributing

Creative Craft is intentionally conservative about new rules.

A contribution should do at least one of the following:

1. improve creative decision quality;
2. make an execution artifact more reproducible;
3. reduce provider-version coupling;
4. strengthen evidence, rights, or delivery integrity;
5. add a tested workflow that is meaningfully different from existing ones.

Provider facts belong in `skills/creative-craft/providers/`, not in the
model-agnostic core. Every capability update must include an official source,
a verification date, and a compatibility note.

Run:

```bash
python3 -m pip install -r requirements-dev.txt
make validate-all
ruff check skills/creative-craft/scripts/creative_craft.py scripts tests
```

Do not add a global rule from one successful output. Add a fixture, describe
the boundary, and distinguish observed behavior from a working hypothesis.
