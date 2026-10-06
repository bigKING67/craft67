# Pi adapter

`package.json` declares:

```json
{"pi":{"skills":["skills/money-craft"]}}
```

Pi can discover the Skill from a package installation. A direct copy is also
available when a user explicitly wants it:

```bash
python3 scripts/install_skill.py --host pi
```

