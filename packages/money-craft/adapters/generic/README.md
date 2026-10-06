# Generic adapter

Hosts that support the Agent Skills convention can consume the canonical
`skills/money-craft` directory. To create a symlink-free copy under an explicit
skills root:

```bash
python3 scripts/install_skill.py --host custom --target-root /path/to/skills
```

