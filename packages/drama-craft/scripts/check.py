#!/usr/bin/env python3
"""Static checks for the drama-craft Skill: frontmatter, links, references, and content invariants.

The check is intentionally offline and dependency-free so it can run in CI. It
verifies structure and the small set of rules that carry the skill's meaning; it
does not judge creative quality. `check_skill` only needs the installed Skill
directory (`skills/drama-craft/`); `check_docs` additionally reads the package
docs, so the two are callable separately.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NAME = 'drama-craft'
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PACKAGE_ROOT / 'skills' / NAME
MAX_SKILL_LINES = 250
MIN_DESCRIPTION = 20
MAX_DESCRIPTION = 1024
MIN_REFERENCE_CHARS = 800

LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
PROTOTYPE = re.compile(r'^#{2,3} P(\d+)\b', re.MULTILINE)
PLACEHOLDERS = ('TODO', 'TBD', 'FIXME', 'XXX', '待补充内容', '待填写')
ABSOLUTE_MARKERS = ('/Users/', '/home/', 'C:\\\\')

REQUIRED_FILES = (
    'SKILL.md',
    'references/story-patterns.md',
    'references/production-craft.md',
    'references/iteration-loop.md',
    'references/output-templates.md',
    'references/worked-example.md',
)

# file -> required phrases that encode a non-negotiable rule
REQUIRED_PHRASES = {
    'references/story-patterns.md': ('固定思路', '情绪路径', '爽点', '主原型', '观察池', '已归类'),
    'references/production-craft.md': ('硬切', '施压', '年龄分层', '生成交接', '参考资产'),
    'references/iteration-loop.md': ('变量矩阵', '停止条件', '单变量', '基线'),
    'references/output-templates.md': ('时间码', '分镜', '机制', '素材来源', '不得直接作为宣称'),
}
IRON_RULES = ('施压者永远不是主角', '主角几乎不反驳', '机制压最后 2–4 秒')
IRON_SECTION = '三条铁律'
# over-claim shapes only: disclaimers such as 不称"已验证" must stay allowed
OVERCLAIM = re.compile(r'\d+ 个已验证|已验证原型')
# the iron rules only bind the prototypes that carry a pressuring role; the Skill must say so
IRON_SCOPE_MARKERS = ('适用范围', '等价硬约束')
# every prototype entry must carry these fields, main prototypes carry two more
PROTOTYPE_FIELDS = ('固定思路', '适配', '生产提示')
MAIN_PROTOTYPE_FIELDS = ('情绪路径', '爽点')
MAIN_PROTOTYPES = (*range(1, 9), 11)
TAXONOMY_MARKERS = ('主原型', '组件', '观察池')


def read_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return {}
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == '---':
            end = index
            break
    if end is None:
        return {}
    data: dict[str, str] = {}
    for line in lines[1:end]:
        if ':' not in line or line[:1] in (' ', '\t', '-'):
            continue
        key, _, value = line.partition(':')
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
            value = value[1:-1]
        data[key.strip()] = value
    return data


def markdown_links(text: str) -> list[str]:
    targets = []
    for raw in LINK.findall(text):
        target = raw.split('#', 1)[0].strip()
        if not target or '://' in target or target.startswith('mailto:'):
            continue
        targets.append(target)
    return targets


def markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob('*.md') if path.is_file())


HEADING = re.compile(r'^(#{1,6})\s')


def section(text: str, keyword: str) -> str:
    """Body of the first heading containing keyword, ending at the next heading of the same level."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = HEADING.match(line)
        if not match or keyword not in line:
            continue
        level = len(match.group(1))
        for end in range(index + 1, len(lines)):
            closing = HEADING.match(lines[end])
            if closing and len(closing.group(1)) <= level:
                return '\n'.join(lines[index + 1:end])
        return '\n'.join(lines[index + 1:])
    return ''


def prototype_bodies(text: str) -> list[tuple[int, str]]:
    """(number, body) for every '## Pn ...' prototype heading, in file order."""
    lines = text.splitlines()
    found: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = PROTOTYPE.match(line)
        if not match:
            continue
        body = []
        for end in range(index + 1, len(lines)):
            if HEADING.match(lines[end]) and len(HEADING.match(lines[end]).group(1)) <= 2:
                break
            body.append(lines[end])
        found.append((int(match.group(1)), '\n'.join(body)))
    return found


def check_skill(root: Path) -> list[str]:
    root = Path(root)
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f'missing file: {relative}')
    if errors:
        return errors

    skill_text = (root / 'SKILL.md').read_text(encoding='utf-8')
    front = read_frontmatter(skill_text)

    name = front.get('name', '')
    if not name:
        errors.append('SKILL.md frontmatter is missing name')
    elif name != root.name:
        errors.append(f'SKILL.md name {name!r} does not match directory {root.name!r}')

    description = front.get('description', '')
    if not description:
        errors.append('SKILL.md frontmatter is missing description')
    else:
        if '\n' in description:
            errors.append('description must stay on one line')
        if not MIN_DESCRIPTION <= len(description) <= MAX_DESCRIPTION:
            errors.append(f'description length {len(description)} outside {MIN_DESCRIPTION}-{MAX_DESCRIPTION}')

    line_count = len(skill_text.splitlines())
    if line_count > MAX_SKILL_LINES:
        errors.append(f'SKILL.md has {line_count} lines, limit is {MAX_SKILL_LINES}')

    for phrase in IRON_RULES:
        if phrase not in skill_text:
            errors.append(f'SKILL.md is missing iron rule: {phrase}')

    iron_body = section(skill_text, IRON_SECTION)
    if not iron_body:
        errors.append(f'SKILL.md is missing the {IRON_SECTION} section')
    else:
        for phrase in IRON_RULES:
            if phrase not in iron_body:
                errors.append(f'iron rule must live in the {IRON_SECTION} section: {phrase}')
        if not any(marker in iron_body for marker in IRON_SCOPE_MARKERS):
            errors.append(f'{IRON_SECTION} must state its 适用范围 or 等价硬约束 for prototypes without a pressuring role')

    for relative, phrases in REQUIRED_PHRASES.items():
        text = (root / relative).read_text(encoding='utf-8')
        if len(text) < MIN_REFERENCE_CHARS:
            errors.append(f'{relative} is too thin ({len(text)} chars)')
        for phrase in phrases:
            if phrase not in text:
                errors.append(f'{relative} is missing required rule: {phrase}')

    prototypes = [int(number) for number in PROTOTYPE.findall((root / 'references/story-patterns.md').read_text(encoding='utf-8'))]
    expected = list(range(1, 12))
    if prototypes != expected:
        errors.append(f'story-patterns.md must define prototypes P1-P11 in order, found {prototypes}')

    patterns_text = (root / 'references/story-patterns.md').read_text(encoding='utf-8')
    for marker in TAXONOMY_MARKERS:
        if marker not in patterns_text:
            errors.append(f'story-patterns.md is missing taxonomy marker: {marker}')
    for number, body in prototype_bodies(patterns_text):
        for field in PROTOTYPE_FIELDS:
            if field not in body:
                errors.append(f'prototype P{number} is missing field: {field}')
        if number in MAIN_PROTOTYPES:
            for field in MAIN_PROTOTYPE_FIELDS:
                if field not in body:
                    errors.append(f'main prototype P{number} is missing field: {field}')

    linked_from_entry = set()
    for target in markdown_links(skill_text):
        normalized = (root / target).resolve()
        if not normalized.is_relative_to(root.resolve()):
            errors.append(f'SKILL.md link escapes the skill directory: {target}')
            continue
        if not normalized.is_file():
            errors.append(f'SKILL.md link target is missing: {target}')
            continue
        linked_from_entry.add(normalized)

    for path in markdown_files(root):
        text = path.read_text(encoding='utf-8')
        relative = path.relative_to(root).as_posix()
        for target in markdown_links(text):
            normalized = (path.parent / target).resolve()
            if not normalized.is_relative_to(root.resolve()):
                errors.append(f'{relative} link escapes the skill directory: {target}')
            elif not normalized.is_file():
                errors.append(f'{relative} link target is missing: {target}')
        for marker in PLACEHOLDERS:
            if marker in text:
                errors.append(f'{relative} contains placeholder marker: {marker}')
        for marker in ABSOLUTE_MARKERS:
            if marker in text:
                errors.append(f'{relative} contains an absolute path: {marker}')

    for reference in sorted((root / 'references').glob('*.md')):
        if reference.resolve() not in linked_from_entry:
            errors.append(f'reference is not linked from SKILL.md: references/{reference.name}')

    return errors


def check_docs(root: Path) -> list[str]:
    """Package docs must track the shipped Skill: version, prototype range and count."""
    root = Path(root)
    errors: list[str] = []
    version_file = root / 'VERSION'
    readme = root / 'README.md'
    changelog = root / 'CHANGELOG.md'
    for path in (version_file, readme, changelog):
        if not path.is_file():
            errors.append(f'missing package doc: {path.name}')
    if errors:
        return errors

    version = version_file.read_text(encoding='utf-8').strip()
    readme_text = readme.read_text(encoding='utf-8')
    changelog_text = changelog.read_text(encoding='utf-8')
    patterns = root / 'skills' / NAME / 'references' / 'story-patterns.md'
    numbers = [int(number) for number in PROTOTYPE.findall(patterns.read_text(encoding='utf-8'))] if patterns.is_file() else []

    if numbers:
        span = f'P{numbers[0]}–P{numbers[-1]}'
        for label, text in (('README.md', readme_text), ('CHANGELOG.md', changelog_text)):
            if span not in text:
                errors.append(f'{label} must reference the prototype range {span}')
            if f'{len(numbers)} 个' not in text:
                errors.append(f'{label} must state the prototype count ({len(numbers)} 个)')

    if f'源码 {version}' not in readme_text:
        errors.append(f'README.md must state the current source version as 源码 {version}')
    if f'## {version}' not in changelog_text:
        errors.append(f'CHANGELOG.md must open a section for {version}')
    if OVERCLAIM.search(readme_text):
        errors.append('README.md must not call the sampled prototypes verified; use 已归类 with an evidence level')
    return errors


def main() -> int:
    if not SKILL_ROOT.is_dir():
        print(json.dumps({'ok': False, 'errors': [f'missing skill directory: {SKILL_ROOT}']}, ensure_ascii=False))
        return 1
    errors = check_skill(SKILL_ROOT) + check_docs(PACKAGE_ROOT)
    patterns = SKILL_ROOT / 'references' / 'story-patterns.md'
    report = {
        'ok': not errors,
        'skill': SKILL_ROOT.name,
        'files': len(markdown_files(SKILL_ROOT)),
        'prototypes': len(PROTOTYPE.findall(patterns.read_text(encoding='utf-8'))) if patterns.is_file() else 0,
        'errors': errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
