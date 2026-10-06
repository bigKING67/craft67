"""Regression tests for the portable runtime's module ownership boundaries."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from support import ROOT

SCRIPTS = ROOT / "skills/creative-craft/scripts"
DOMAIN_MODULES = {
    "creative_craft_contracts",
    "creative_craft_entrypoint",
    "creative_craft_evaluation",
    "creative_craft_packs",
    "creative_craft_project",
    "creative_craft_project_ops",
    "creative_craft_runtime",
    "creative_craft_video",
}


def creative_craft_imports(path: Path) -> set[str]:
    imports: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name
                for alias in node.names
                if alias.name.startswith("creative_craft")
            )
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("creative_craft")
        ):
            imports.add(node.module)
    return imports


class RuntimeArchitectureTests(unittest.TestCase):
    def test_public_entrypoint_is_a_logic_free_compatibility_facade(self) -> None:
        facade = SCRIPTS / "creative_craft.py"
        tree = ast.parse(facade.read_text(encoding="utf-8"), filename=str(facade))

        self.assertFalse(
            any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                for node in tree.body
            )
        )
        self.assertEqual(DOMAIN_MODULES, creative_craft_imports(facade))

    def test_domain_dependency_graph_is_acyclic_and_never_imports_facade(self) -> None:
        raw_graph = {
            module: creative_craft_imports(SCRIPTS / f"{module}.py")
            for module in DOMAIN_MODULES
        }
        graph = {
            module: dependencies & DOMAIN_MODULES
            for module, dependencies in raw_graph.items()
        }
        for module, dependencies in raw_graph.items():
            self.assertNotIn("creative_craft", dependencies, module)
            if module != "creative_craft_entrypoint":
                self.assertNotIn("creative_craft_entrypoint", dependencies, module)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module: str) -> None:
            if module in visiting:
                self.fail(f"runtime module dependency cycle includes {module}")
            if module in visited:
                return
            visiting.add(module)
            for dependency in graph[module]:
                visit(dependency)
            visiting.remove(module)
            visited.add(module)

        for module in sorted(graph):
            visit(module)
