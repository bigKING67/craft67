#!/usr/bin/env python3
"""Deterministic structural check of a drama-craft delivery against the eval rubric.

The checker only verifies the contract that the Skill itself states: required
sections, shot-table columns, generation-handoff fields, dialogue length, shot
duration, single-variable matrices, and a mechanism that carries a number. It
does not judge taste, castability beyond those fields, or real ad performance.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'evals' / 'cases'
BASELINES = ROOT / 'evals' / 'baselines'

FRONTMATTER = re.compile(r'^---\n(.*?)\n---\n', re.S)
SHOT_HEADER = ('镜号', '时间码', '时长', '景别', '画面', '台词', '音效', '卖点', '素材来源', '参考资产', '生成要点', '风险')
SOURCE_VALUES = {'AI', '实拍', '图库'}
ASSET = re.compile(r'(CH|SC|PD)-\d{2}')
TIME = re.compile(r'^(\d+(?:\.\d+)?)\s*[–\-—]\s*(\d+(?:\.\d+)?)$')
DURATION = re.compile(r'^(\d+(?:\.\d+)?)\s*s?$')
NO_ASSET = {'—', '-', '–', ''}
STRIP = '，。！？、；：“”‘’（）()「」【】…—*`\'"!?.,;: '
MAX_DIALOGUE_CHARS = 12
MAX_SHOT_SECONDS = 5.0
MAIN_PROTOTYPES = {f'P{number}' for number in (*range(1, 9), 11)}


def parse_case(path: Path) -> dict[str, object]:
    text = path.read_text(encoding='utf-8')
    match = FRONTMATTER.match(text)
    if not match:
        raise ValueError(f'{path.name}: missing frontmatter')
    data: dict[str, object] = {'case': path.stem}
    for line in match.group(1).splitlines():
        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        key, value = key.strip(), value.strip()
        if value.lower() in {'true', 'false'}:
            data[key] = value.lower() == 'true'
        elif re.fullmatch(r'\d+', value):
            data[key] = int(value)
        elif ',' in value or '，' in value:
            data[key] = [item.strip() for item in re.split(r'[,，]', value) if item.strip()]
        else:
            data[key] = value
    return data


def split_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = ''
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith('## '):
            sections.append((heading, '\n'.join(body)))
            heading, body = line[3:].strip(), []
        else:
            body.append(line)
    sections.append((heading, '\n'.join(body)))
    return sections


def tables(text: str) -> list[dict[str, list]]:
    found: list[dict[str, list]] = []
    lines = [line.strip() for line in text.splitlines()]
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith('|') and index + 1 < len(lines) and re.fullmatch(r'\|[\s:|-]+\|', lines[index + 1]):
            header = [cell.strip() for cell in line.strip('|').split('|')]
            rows: list[list[str]] = []
            cursor = index + 2
            while cursor < len(lines) and lines[cursor].startswith('|'):
                rows.append([cell.strip() for cell in lines[cursor].strip('|').split('|')])
                cursor += 1
            found.append({'header': header, 'rows': rows})
            index = cursor
        else:
            index += 1
    return found


def normalized(cell: str) -> str:
    """Column name without the template's inline annotation, e.g. 画面（动作 + 场景 + 光线） -> 画面."""
    return re.split(r'[（(/]', cell)[0].strip()


def dialogue_chars(cell: str) -> int:
    value = re.sub(r'（[^）]*）|\([^)]*\)', '', cell)
    if '：' in value:
        value = value.split('：', 1)[1]
    elif ':' in value:
        value = value.split(':', 1)[1]
    return len([char for char in value if char not in STRIP])


def check_shot_table(number: int, table: dict[str, list], errors: list[str]) -> None:
    header = table['header']
    index = {normalized(cell): position for position, cell in enumerate(header)}
    missing = [name for name in SHOT_HEADER if name not in index]
    unknown = [name for name in index if name not in SHOT_HEADER]
    if missing:
        errors.append(f'table {number}: shot table is missing columns {missing}')
        return
    if unknown:
        errors.append(f'table {number}: shot table has unknown columns {unknown}; use the template columns')
    if not table['rows']:
        errors.append(f'table {number}: shot table has no rows')
        return
    previous_end = None
    for row_number, row in enumerate(table['rows'], start=2):
        where = f'table {number} row {row_number}'
        if len(row) != len(header):
            errors.append(f'{where}: expected {len(header)} cells, found {len(row)}')
            continue
        shot = {name: row[index[name]] for name in SHOT_HEADER}
        timecode = TIME.fullmatch(shot['时间码'].replace(' ', ''))
        if not timecode:
            errors.append(f'{where}: 时间码 must look like 0.0–2.0, found {shot["时间码"]!r}')
        else:
            start, end = float(timecode.group(1)), float(timecode.group(2))
            if end <= start:
                errors.append(f'{where}: 时间码 end must be after start ({shot["时间码"]})')
            if previous_end is not None and abs(start - previous_end) > 1e-6:
                errors.append(f'{where}: 时间码 is not contiguous with the previous shot ({previous_end} -> {start})')
            previous_end = end
        duration = DURATION.fullmatch(shot['时长'].replace(' ', ''))
        if not duration:
            errors.append(f'{where}: 时长 must look like 2.0s, found {shot["时长"]!r}')
        elif float(duration.group(1)) > MAX_SHOT_SECONDS:
            errors.append(f'{where}: 时长 {shot["时长"]} exceeds the {MAX_SHOT_SECONDS:g}s generation grid')
        if shot['素材来源'] not in SOURCE_VALUES:
            errors.append(f'{where}: 素材来源 must be one of {sorted(SOURCE_VALUES)}, found {shot["素材来源"]!r}')
        assets = shot['参考资产']
        if assets not in NO_ASSET:
            tokens = [token for token in re.split(r'[\s/、,，]+', assets) if token]
            bad = [token for token in tokens if not ASSET.fullmatch(token)]
            if bad:
                errors.append(f'{where}: 参考资产 must use CH/SC/PD numbers, found {bad}')
        if '字幕' not in shot['台词']:
            chars = dialogue_chars(shot['台词'])
            if chars > MAX_DIALOGUE_CHARS:
                errors.append(f'{where}: 台词 has {chars} characters, limit is {MAX_DIALOGUE_CHARS}')
        for field in ('画面', '台词', '生成要点', '风险'):
            if not shot[field]:
                errors.append(f'{where}: {field} must not be empty')


def check_mechanism(table: dict[str, list], errors: list[str]) -> None:
    header, rows = table['header'], table['rows']
    if not rows:
        return
    index = {normalized(cell): position for position, cell in enumerate(header)}
    if '台词' not in index or '画面' not in index:
        return
    dialogue, picture = index['台词'], index['画面']
    target = rows[-1]
    for row in rows:
        if any('机制' in cell for cell in row):
            target = row
            break
    text = target[dialogue] + target[picture]
    if not re.search(r'\d', text):
        errors.append('mechanism beat carries no number; the 机制收口 must include a concrete figure')


def check_matrix(sections: list[tuple[str, str]], errors: list[str]) -> None:
    for heading, body in sections:
        if '变量矩阵' not in heading and '变量矩阵' not in body:
            continue
        for number, table in enumerate(tables(body), start=1):
            header, rows = table['header'], table['rows']
            normalized_header = [normalized(cell) for cell in header]
            if '编号' not in normalized_header or not rows:
                continue
            if '本轮状态' not in normalized_header:
                errors.append('变量矩阵 is missing the 本轮状态 column')
                continue
            if '原型' not in normalized_header:
                errors.append('变量矩阵 is missing the 原型 column')
                continue
            header = normalized_header
            state, prototype = header.index('本轮状态'), header.index('原型')
            identifier = header.index('编号')
            if '基线' not in rows[0][state]:
                errors.append('变量矩阵 must mark the first row as 基线')
            for index in range(1, len(rows)):
                before, after = rows[index - 1], rows[index]
                if len(before) != len(after):
                    errors.append(f'变量矩阵 row {index + 2} has {len(after)} cells, expected {len(before)}')
                    continue
                changed = [header[column] for column in range(len(header))
                           if column not in (state, identifier) and before[column] != after[column]]
                if len(changed) != 1:
                    errors.append(f'变量矩阵 row {index + 2} changes {len(changed)} columns {changed}; a round may change exactly one')
            for row in rows:
                value = row[prototype]
                if value not in MAIN_PROTOTYPES:
                    errors.append(f'变量矩阵 原型 {value!r} is not a main prototype (P1–P8, P11); components are not tested as directions')
            return


def check_delivery(case: dict[str, object], text: str) -> list[str]:
    errors: list[str] = []
    sections = split_sections(text)
    headings = [heading for heading, _ in sections]

    for keyword in case.get('require_sections', []) or []:
        if not any(keyword in heading or keyword in body for heading, body in sections):
            errors.append(f'required section or content missing: {keyword}')

    minimum = int(case.get('min_directions', 0) or 0)
    if minimum:
        found = [heading for heading in headings if '方向' in heading]
        if len(found) < minimum:
            errors.append(f'expected at least {minimum} directions, found {len(found)}')

    shot_tables = [table for _, body in sections for table in tables(body)
                   if any(normalized(cell) == '镜号' for cell in table['header'])]
    if case.get('forbid_shot_tables') and shot_tables:
        errors.append('this deliverable must not ship a shot table; it only asks for candidates')
    if case.get('require_shot_tables') and not shot_tables:
        errors.append('this deliverable requires at least one shot table')

    for number, table in enumerate(shot_tables, start=1):
        check_shot_table(number, table, errors)
        check_mechanism(table, errors)

    if case.get('require_frozen_invariants') and '冻结不变量' not in text:
        errors.append('required section or content missing: 冻结不变量')
    check_matrix(sections, errors)
    return errors


def run_all(require_coverage: int | None = None) -> dict[str, object]:
    results = []
    covered = set()
    for baseline in sorted(BASELINES.glob('*.md')):
        case_path = CASES / f'{baseline.stem}.md'
        if not case_path.is_file():
            results.append({'case': baseline.stem, 'ok': False, 'errors': [f'no case file for {case_path.name}']})
            continue
        covered.add(baseline.stem)
        case = parse_case(case_path)
        errors = check_delivery(case, baseline.read_text(encoding='utf-8'))
        results.append({'case': baseline.stem, 'ok': not errors, 'errors': errors})
    case_ids = sorted(path.stem for path in CASES.glob('*.md'))
    uncovered = [case_id for case_id in case_ids if case_id not in covered]
    errors = [f'uncovered case without a baseline: {case_id}' for case_id in uncovered] if require_coverage and len(covered) < require_coverage else []
    return {
        'ok': not errors and all(result['ok'] for result in results),
        'cases': case_ids,
        'covered': sorted(covered),
        'uncovered': uncovered,
        'results': results,
        'errors': errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', help='case markdown file')
    parser.add_argument('--output', help='delivery markdown to check')
    parser.add_argument('--all', action='store_true', help='check every baseline that exists')
    parser.add_argument('--require-coverage', type=int, help='fail when fewer baselines than this exist')
    args = parser.parse_args()

    if args.all:
        report = run_all(args.require_coverage)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return int(not report['ok'])

    if not args.case or not args.output:
        parser.error('use --all, or both --case and --output')

    case = parse_case(Path(args.case))
    errors = check_delivery(case, Path(args.output).read_text(encoding='utf-8'))
    print(json.dumps({'ok': not errors, 'case': case.get('case'), 'output': args.output, 'errors': errors},
                     ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
