# Premium haircare launch example

Fictional project used to demonstrate Creative Craft contracts. No real brand,
claim, person, product image, or licensed reference is included.

Selected route: `Motion Is Proof`.

The example contains:

- a locked brief;
- three distinct concept routes;
- an asset ledger with fictional source records;
- a locked Creative Direction;
- GPT Image 2 and Seedance 2.5 Job v2 artifacts with explicit execution surfaces;
- an evidence-bound direction-stage Evaluation v2;
- a planned Delivery v2 manifest;
- a Project Manifest binding every registered artifact by SHA-256.

It deliberately contains no Execution Receipt, Output Inspection, generated
file, or approval claim. Synthetic lifecycle evidence exists only in tests.

Compile:

```bash
python3 skills/creative-craft/scripts/creative_craft.py compile-image \
  --file examples/premium-haircare-launch/image-job.json

python3 skills/creative-craft/scripts/creative_craft.py compile-video \
  --file examples/premium-haircare-launch/video-job.json

python3 skills/creative-craft/scripts/creative_craft.py validate-project \
  --root examples/premium-haircare-launch

python3 skills/creative-craft/scripts/creative_craft.py score \
  --file examples/premium-haircare-launch/evaluation.json \
  --root examples/premium-haircare-launch
```
