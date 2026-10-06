#!/usr/bin/env python3
"""Audit saved Codex task evidence; machine checks never certify research semantics."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/money-craft/scripts'))
from financial_rigor import audit_text


def public_citations(answer: str, case: dict) -> tuple[list[dict], list[str]]:
    """Check explicit case-required source links, not source truth or claim support.

    Accept source-labelled inline links and single-line source definitions.
    Exact registered HTTPS URLs are required; this performs no network access.
    """
    required = case['machine_contract'].get('public_source_ids', [])
    if not isinstance(required, list) or any(not isinstance(s, str) or not re.fullmatch(r'S\d+', s) for s in required):
        return [], ['INVALID_PUBLIC_SOURCE_CONTRACT']
    visible = re.sub(r'<!--.*?(?:-->|\Z)', '', answer, flags=re.DOTALL)
    visible = re.sub(r'^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?(?:^ {0,3}\1[ \t]*$|\Z)', '', visible,
                     flags=re.MULTILINE | re.DOTALL)
    visible = re.sub(r'`[^`\n]*`', '', visible)
    links = re.findall(r'\[(S\d+)(?:[^\]\n]*)\]\(<?([^\s<>\)]+)>?\)', visible)
    links += re.findall(r'^\[(S\d+)\]:?[ \t]+<?(https://[^\s<>]+)>?[ \t]*$', visible, re.MULTILINE)
    checks, errors = [], []
    for source_id in dict.fromkeys(required):
        sources = [s for s in case.get('evidence', []) if s['source_id'] == source_id]
        allowed = {s.get(k) for s in sources for k in ('url', 'final_url')
                   if isinstance(s.get(k), str) and s[k].startswith('https://')}
        targets = [url for sid, url in links if sid == source_id]
        local_targets = set()
        for source in sources:
            path = source.get('path')
            if isinstance(path, str) and path:
                local_targets.add(str(ROOT / path))
                local_targets.add(str((ROOT / path).resolve()))
        # A registered local artifact may accompany its public citation. It
        # never satisfies the public-link requirement by itself, and unrelated
        # local or public targets still invalidate the source identity.
        matched = (len(sources) == 1 and bool(allowed)
                   and any(url in allowed for url in targets)
                   and all(url in allowed or url in local_targets for url in targets))
        checks.append({'source_id': source_id, 'registered_public_link': matched})
        if not matched:
            errors.append('PUBLIC_SOURCE_LINK_NOT_VERIFIED:'+source_id)
    return checks, errors


def route_command(command: str) -> bool:
    """Recognize simple direct/shell-wrapped invocations, never execute trace text."""
    if not isinstance(command, str):
        return False
    try:
        tokens = shlex.split(command)
        if len(tokens) == 3 and Path(tokens[0]).name in {'zsh', 'bash', 'sh'} and tokens[1] in {'-lc', '-c'}:
            # Existing host traces can prefix the route with a date command.
            lines = tokens[2].strip().splitlines()
            tokens = shlex.split(lines[-1]) if lines else []
        # Hosts can disable bytecode without changing the route invocation.
        # Accept this exact assignment only, not arbitrary environment overrides.
        if tokens and tokens[0] == 'PYTHONDONTWRITEBYTECODE=1':
            tokens = tokens[1:]
        if tokens and Path(tokens[0]).name in {'bash', 'sh'}:
            tokens = tokens[1:]
        elif tokens and re.fullmatch(r'python(?:3(?:\.\d+)?)?', Path(tokens[0]).name):
            # The shell entrypoint execs this core; -B only disables bytecode.
            # Reject -c/-m, arbitrary interpreter flags and unrelated scripts.
            tokens = tokens[1:]
            if tokens and tokens[0] == '-B':
                tokens = tokens[1:]
            if not tokens or Path(tokens[0]).name != 'investment_route_core.py':
                return False
            tokens = ['investment_route_plan.sh', *tokens[1:]]
        return bool(tokens and Path(tokens[0]).name == 'investment_route_plan.sh'
                    and '--help' not in tokens and '--output' in tokens
                    and not any(c in t for t in tokens for c in ';|&<>`$'))
    except ValueError:
        return False


def route_payload(output: str) -> dict | None:
    # Permit a preceding date line, but not trailing output or multiple receipts.
    if not isinstance(output, str):
        return None
    decoder = json.JSONDecoder()
    for pos, char in enumerate(output):
        if char != '{':
            continue
        try:
            value, end = decoder.raw_decode(output[pos:])
        except ValueError:
            continue
        if (isinstance(value, dict) and value.get('schema') == 'codex.investment-route.v2'
                and not output[pos + end:].strip()):
            return value
    return None



def portfolio_receipts(answer: str, commands: list[dict]) -> tuple[str, list[str]]:
    """Accept native portfolio receipts only when bound to observed successful output.

    This verifies output parity and arithmetic, not invocation authenticity or
    source semantics; those remain part of the host trace/manual review.
    """
    def strict_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def decode(raw):
        return json.loads(raw, object_pairs_hook=strict_object)

    blocks = re.findall(r"^```json[ \t]*\n(.*?)^```[ \t]*$", answer, re.MULTILINE | re.DOTALL)
    receipts, errors = [], []
    for block in blocks:
        try:
            value = decode(block)
        except ValueError:
            if 'money-craft.portfolio-audit.v1' in block:
                errors.append('INVALID_PORTFOLIO_RESULT_JSON')
            continue
        if not isinstance(value, dict) or value.get('schema') != 'money-craft.portfolio-audit.v1':
            continue
        # Rejected inputs have no arithmetic to audit; their error semantics remain manual.
        if value.get('valid') is False and 'calculations' not in value:
            continue
        if value.get('valid') is not True or not isinstance(value.get('calculations'), list) or not value['calculations']:
            errors.append('INVALID_PORTFOLIO_CALCULATIONS')
            continue
        canonical = json.dumps(value, sort_keys=True, ensure_ascii=False)
        matched = False
        for item in commands:
            if item.get('exit_code') != 0:
                continue
            try:
                observed = decode(item.get('aggregated_output', ''))
            except (ValueError, TypeError):
                continue
            if json.dumps(observed, sort_keys=True, ensure_ascii=False) == canonical:
                matched = True
                break
        if not matched:
            errors.append('PORTFOLIO_RESULT_NOT_BOUND_TO_TRACE')
            continue
        receipts.extend('<!-- money-craft-calc: ' + json.dumps(c) + ' -->' for c in value['calculations'])
    # A concise answer may cite a canonical input digest instead of repeating
    # the full result. Accept only the explicitly declared encoding we verify.
    if not receipts and not errors and not audit_text(answer)['checks']:
        bound_results = 0
        for item in commands:
            if item.get('exit_code') != 0:
                continue
            try:
                value = decode(item.get('aggregated_output', ''))
            except (ValueError, TypeError):
                continue
            if (not isinstance(value, dict) or value.get('schema') != 'money-craft.portfolio-audit.v1'
                    or value.get('valid') is not True or not isinstance(value.get('input'), dict)
                    or value.get('input_hash_encoding') != 'UTF-8 JSON ensure_ascii=False sort_keys=True separators=(comma,colon)'
                    or not isinstance(value.get('calculations'), list) or not value['calculations']):
                continue
            try:
                digest = hashlib.sha256(json.dumps(value['input'], ensure_ascii=False,
                    sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
            except (ValueError, TypeError):
                errors.append('INVALID_PORTFOLIO_INPUT_DIGEST')
                continue
            if value.get('input_sha256') != digest or not re.search(r'(?<![0-9a-f])'+digest+r'(?![0-9a-f])', answer):
                continue
            bound_results += 1
            receipts.extend('<!-- money-craft-calc: ' + json.dumps(c) + ' -->' for c in value['calculations'])
        if bound_results > 1:
            errors.append('AMBIGUOUS_PORTFOLIO_RESULT')
    return '\n'.join(receipts), errors


def audit(run_dir: Path, case: dict) -> dict:
    errors = []
    host = json.loads((run_dir / 'host.json').read_text())
    if not isinstance(host, dict) or not isinstance(host.get('artifact_hashes'), dict):
        raise ValueError('invalid host artifact manifest')
    if host.get('case_id') != case['id']:
        errors.append('CASE_ID_MISMATCH')
    if host.get('exit_code') != 0 or host.get('timed_out') is not False:
        errors.append('HOST_NOT_COMPLETED')
    hashes = host.get('artifact_hashes', {})
    for name in ('answer.md', 'events.jsonl'):
        digest = hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
        if hashes.get(name) != digest:
            errors.append(f'ARTIFACT_HASH_MISMATCH:{name}')
    answer = (run_dir / 'answer.md').read_text()
    if not answer.strip():
        errors.append('EMPTY_ANSWER')
    evidence_checks = []
    for source in case.get('evidence', []):
        source_id = source['source_id']
        evidence_path = ROOT / source['path']
        try:
            digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            matched = digest == source['sha256']
        except OSError:
            matched = False
        evidence_checks.append({'source_id': source_id, 'hash_verified': matched})
        if not matched:
            errors.append(f'SOURCE_EVIDENCE_NOT_VERIFIED:{source_id}')
    commands = []
    for line in (run_dir / 'events.jsonl').read_text().splitlines():
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError('event must be an object')
        item = event.get('item', {})
        if event.get('type') == 'item.completed' and isinstance(item, dict) and item.get('type') == 'command_execution':
            commands.append(item)
    policy = case['machine_contract']
    citation_checks, citation_errors = public_citations(answer, case)
    errors.extend(citation_errors)
    attempts = []
    for item in commands:
        if not route_command(item.get('command', '')):
            continue
        payload = route_payload(item.get('aggregated_output', ''))
        state = 'INVALID'
        if item.get('exit_code') == 0 and payload:
            classification = payload.get('classification')
            structure = (isinstance(classification, dict) and isinstance(classification.get('intent'), str)
                         and bool(classification['intent']) and isinstance(payload.get('route_id'), str)
                         and bool(payload['route_id']) and isinstance(payload.get('stage_chain'), list)
                         and bool(payload['stage_chain'])
                         and all(isinstance(stage, dict) and isinstance(stage.get('name'), str)
                                 and bool(stage['name']) for stage in payload['stage_chain']))
            if structure and payload.get('status') == 'ready' and payload.get('error_code') is None:
                state = 'READY'
            elif structure and payload.get('status') == 'needs_input' and payload.get('error_code') in policy.get('allowed_route_blocks', []):
                state = 'BLOCKED_AS_EXPECTED'
        attempts.append({'exit_code': item.get('exit_code'), 'state': state,
                         'error_code': payload.get('error_code') if payload else None})
    route_state = attempts[-1]['state'] if attempts else 'NOT_OBSERVED'
    if policy['route_required'] and route_state not in {'READY', 'BLOCKED_AS_EXPECTED'}:
        errors.append('ROUTE_REQUIRED_NOT_VERIFIED')
    if attempts and route_state == 'INVALID':
        errors.append('LAST_ROUTE_ATTEMPT_INVALID')
    native_receipts, native_errors = portfolio_receipts(answer, commands)
    errors.extend(native_errors)
    financial = audit_text(answer + "\n" + native_receipts)
    if not financial['valid']:
        errors.append('FINANCIAL_AUDIT_FAILED')
    if policy['calculations_required'] and not financial['checks']:
        errors.append('CALCULATION_RECEIPTS_REQUIRED')
    return {'schema': 'money-craft.skill-task-machine-audit.v1', 'case_id': case['id'],
            'machine_checks_pass': not errors, 'research_complete': False,
            'semantic_verdict': 'REQUIRES_MANUAL_REVIEW',
            'route': {'state': route_state, 'attempts': attempts, 'ready': route_state == 'READY'},
            'financial': financial, 'source_evidence': evidence_checks,
            'public_citations': citation_checks, 'errors': errors,
            'manual_criteria': [{'criterion': c, 'status': 'PENDING'} for c in case['criteria']],
            'input_hashes': {n: hashlib.sha256((run_dir / n).read_bytes()).hexdigest()
                             for n in ('host.json', 'events.jsonl', 'answer.md')},
            'case_contract_sha256': hashlib.sha256(json.dumps(case, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}


def load_run_case(run_dir: Path, case_file: Path | None) -> dict:
    """Default to the hash-bound contract actually used, including runner defaults."""
    host = json.loads((run_dir / 'host.json').read_text())
    if case_file is None:
        snapshot = run_dir / 'case-snapshot.json'
        expected = host.get('artifact_hashes', {}).get('case-snapshot.json')
        if expected is not None:
            if hashlib.sha256(snapshot.read_bytes()).hexdigest() != expected:
                raise ValueError('case snapshot hash mismatch')
            case = json.loads(snapshot.read_text())
            if case['id'] != host['case_id']:
                raise ValueError('case snapshot identity mismatch')
            return case
        if snapshot.exists():
            raise ValueError('case snapshot is not bound to host')
        case_file = ROOT / 'acceptance/skill-tasks/cases.json'
    cases = json.loads(case_file.read_text())['cases']
    matches = [c for c in cases if c['id'] == host['case_id']]
    if len(matches) != 1:
        raise ValueError('case identity is absent or ambiguous')
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--case-file', type=Path, help='Explicit alternate contract; default is the bound run snapshot')
    args = parser.parse_args()
    try:
        case = load_run_case(args.run_dir, args.case_file)
        result = audit(args.run_dir, case)
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        result = {'schema': 'money-craft.skill-task-machine-audit.v1', 'machine_checks_pass': False,
                  'research_complete': False, 'errors': [f'INVALID_INPUT:{type(exc).__name__}']}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['machine_checks_pass'] else 4


if __name__ == '__main__':
    raise SystemExit(main())
