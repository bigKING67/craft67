/** Optional Pi UI adapter. Reads project configuration; never sends model context or replaces the footer. */
import { execFile } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const script = fileURLToPath(new URL('../../scripts/workflow_status.py', import.meta.url));
const labels = new Set(['Workflow: solo', 'Workflow: team', 'Workflow: 未配置', 'Workflow: 配置错误', 'Workflow: 不可用']);

type Context = { cwd: string; hasUI: boolean; ui: { setStatus(key: string, value: string | undefined): void } };
type Host = { on(event: 'session_start' | 'agent_end' | 'session_shutdown', handler: (event: unknown, context: Context) => void | Promise<void>): void };

export default function workflowStatus(pi: Host) {
  let generation = 0;
  const refresh = async (_event: unknown, ctx: Context) => {
    const current = ++generation;
    if (!ctx.hasUI) return;
    const label = await new Promise<string>((resolve) => {
      execFile(process.env.WORKFLOW_CRAFT_PYTHON || 'python3', ['-B', script, '--project', ctx.cwd],
        { cwd: ctx.cwd, timeout: 1500, maxBuffer: 4096, windowsHide: true }, (error, stdout) => {
          const value = stdout.trim();
          resolve(!error && labels.has(value) ? value : 'Workflow: 不可用');
        });
    });
    if (current === generation) ctx.ui.setStatus('workflow-craft', label);
  };
  // Pi 1.4+ emits session_start for startup, reload, new, resume and fork.
  pi.on('session_start', refresh);
  pi.on('agent_end', refresh);
  pi.on('session_shutdown', (_event, ctx) => {
    generation++;
    if (ctx.hasUI) ctx.ui.setStatus('workflow-craft', undefined);
  });
}
