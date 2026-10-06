#!/usr/bin/env python3
"""Run one explicit-source or implicit Skill behavioral case in an isolated Codex session.

Records host evidence only. A successful process is never a semantic PASS.
"""
import argparse
import copy
import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time

from audit_skill_task import audit
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def prepare_case(original: dict) -> dict:
    """Freeze defaults for new runs without changing the stored source case."""
    case = copy.deepcopy(original)
    case['machine_contract'].setdefault('public_source_ids', [
        s['source_id'] for s in case.get('evidence', [])
        if any(isinstance(s.get(key), str) and s[key].startswith('https://')
               for key in ('url', 'final_url'))])
    return case


def citation_instruction(case: dict) -> str:
    required = case['machine_contract'].get('public_source_ids', [])
    if not required:
        return ''
    return ('\n最终来源索引须为 '+', '.join(required)+
            ' 提供登记的公开HTTPS链接，采用 [S01 来源名称](URL) 或单行 [S01]: URL 格式；'
            '本机证据路径用于复核，不能代替公开来源链接。')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',required=True)
    parser.add_argument('--case-file', type=Path, default=ROOT/'acceptance/skill-tasks/cases.json')
    parser.add_argument('--output-dir',required=True,type=Path)
    parser.add_argument('--timeout',type=int,default=150)
    parser.add_argument('--invocation', choices=('explicit-source', 'implicit'), default='explicit-source')
    args=parser.parse_args()
    if not 10 <= args.timeout <= 900:parser.error('timeout must be 10..900 seconds')
    cases=json.loads(args.case_file.read_text())['cases']
    selected=[c for c in cases if c['id']==args.case]
    if len(selected)!=1 or selected[0]['status'] not in {'READY_SYNTHETIC', 'READY_HISTORICAL'}:parser.error('case is absent or not ready')
    case=prepare_case(selected[0]);out=args.output_dir.resolve()
    materials = case['facts']
    for source in case.get('evidence', []):
        evidence_path = (ROOT / source['path']).resolve()
        if hashlib.sha256(evidence_path.read_bytes()).hexdigest() != source['sha256']:
            parser.error(f"evidence hash mismatch: {source['source_id']}")
        materials += '\n' + json.dumps({**source, 'path':str(evidence_path)},ensure_ascii=False)
    out.mkdir(parents=True,exist_ok=False)
    skill=ROOT/'skills/money-craft/SKILL.md'
    task_kind = '历史正式资料回放' if case['status']=='READY_HISTORICAL' else '离线合成任务'
    instruction=f'这是Money Craft的{task_kind}。显式使用源码Skill：{skill}。先读取该Skill及本任务需要的引用。' if args.invocation=='explicit-source' else f'这是{task_kind}。'
    prompt=f'{instruction}禁止联网取真实资料、账户/交易动作、修改项目或全局配置；仅对下面指定的材料回答。无需正式归档。不得读取acceptance测试标准或其他会话答案。\n\n用户问题：{case["prompt"]}\n材料：{materials}\n请给最终中文回答，并简要列出实际读取的Skill引用。'
    prompt += citation_instruction(case)
    (out/'prompt.txt').write_text(prompt)
    (out/'case-snapshot.json').write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n')
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'skills/money-craft').rglob('*')) if p.is_file() and p.suffix in {'.md','.py','.json'}}
    installed=Path.home()/'.agents/skills/money-craft'
    installed_hashes={str(p.relative_to(installed)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(installed.rglob('*')) if p.is_file() and p.suffix in {'.md','.py','.json'}} if args.invocation=='implicit' else {}
    with tempfile.TemporaryDirectory(prefix='money-skill-task-') as cwd:
        argv=['codex','exec','--ephemeral','--sandbox','read-only','--skip-git-repo-check','-C',cwd,'--json','-o',str(out/'answer.md'),'-']
        with (out/'events.jsonl').open('w') as stdout,(out/'stderr.txt').open('w') as stderr:
            started = time.monotonic()
            process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,start_new_session=True)
            timed_out=False
            try:process.communicate(prompt,timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out=True
                os.killpg(process.pid,signal.SIGKILL)
                process.communicate()
            elapsed_seconds = round(time.monotonic() - started, 3)
    commands=[]
    for line in (out/'events.jsonl').read_text().splitlines():
        try:event=json.loads(line)
        except ValueError:continue
        item=event.get('item',{})
        if event.get('type')=='item.completed' and item.get('type')=='command_execution':
            commands.append({'command':item.get('command'),'exit_code':item.get('exit_code')})
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
    result={'schema':'money-craft.skill-task-host.v1','case_id':case['id'],'exit_code':process.returncode,'timed_out':timed_out,
        'timeout_seconds':args.timeout,'elapsed_seconds':elapsed_seconds,
        'invocation':'EXPLICIT_SOURCE_PATH' if args.invocation=='explicit-source' else 'IMPLICIT_NATURAL_PROMPT','automatic_discovery':'NOT_TESTED' if args.invocation=='explicit-source' else 'REQUIRES_TRACE_REVIEW','semantic_verdict':'REQUIRES_MANUAL_REVIEW',
        'answer_present':(out/'answer.md').is_file(),'commands':commands,'artifact_hashes':files,'source_hashes':hashes,'installed_skill_root':str(installed) if installed_hashes else None,'installed_hashes':installed_hashes}
    (out/'host.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    try:
        machine = audit(out, case) if result['answer_present'] else {'machine_checks_pass':False,'research_complete':False,'errors':['ANSWER_MISSING']}
    except (OSError, ValueError, KeyError, TypeError):
        machine = {'machine_checks_pass':False,'research_complete':False,'errors':['INVALID_AUDIT_INPUT']}
    (out/'machine-audit.json').write_text(json.dumps(machine,ensure_ascii=False,indent=2)+'\n')
    result['machine_checks_pass'] = machine['machine_checks_pass']
    print(json.dumps({k:result[k] for k in ('case_id','exit_code','timed_out','answer_present','semantic_verdict','machine_checks_pass')},ensure_ascii=False))
    return 0 if machine['machine_checks_pass'] else 4

if __name__=='__main__':raise SystemExit(main())
