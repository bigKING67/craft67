#!/usr/bin/env node
// 导出只含运行所需文件的 skill 分发目录；验收样例、质量记录、测试与研究扫描件留在仓库。
// 用法：npm run pack:skill -- <目标目录>（目标须不存在，不覆盖）。
import { execSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const target = process.argv[2];
if (!target) {
  console.error("用法：npm run pack:skill -- <目标目录>");
  process.exit(2);
}
// npm run 会把 cwd 切到仓库根；相对路径按用户执行命令时的目录解析。
const out = resolve(process.env.INIT_CWD ?? process.cwd(), target);
if (existsSync(out)) {
  console.error(`目标已存在，不覆盖：${out}`);
  process.exit(1);
}
if (out === root || out.startsWith(`${root}${sep}`)) {
  console.error(`目标不能位于仓库内：${out}`);
  process.exit(1);
}
// 清空 dist 后按当前 src 重建，避免过期或已删除模块的产物进入分发包。
rmSync(join(root, "dist"), { recursive: true, force: true });
execSync("npm run build", { cwd: root, stdio: "inherit" });

const include = [
  "SKILL.md",
  "README.md",
  "LICENSE",
  "THIRD_PARTY_NOTICES.md",
  "package.json",
  "package-lock.json",
  "tsconfig.json",
  "references",
  "src",
  "dist",
  "examples/birth.json",
  "examples/report.md",
  "examples/followups.md",
  // SKILL.md 链接研究索引；只带顶层说明文档，不带扫描图片与校勘数据。
  ...readdirSync(join(root, "docs/research"))
    .filter((name) => name.endsWith(".md"))
    .map((name) => `docs/research/${name}`),
];

// 全部清单项存在后才创建目标目录，失败时不留下半成品。
const missing = include.filter((rel) => !existsSync(join(root, rel)));
if (missing.length) {
  console.error(`缺少文件：${missing.join("、")}`);
  process.exit(1);
}
mkdirSync(out, { recursive: true });
let bytes = 0;
const walk = (path) =>
  statSync(path).isDirectory()
    ? readdirSync(path).reduce((sum, name) => sum + walk(join(path, name)), 0)
    : statSync(path).size;
for (const rel of include) {
  const from = join(root, rel);
  mkdirSync(dirname(join(out, rel)), { recursive: true });
  cpSync(from, join(out, rel), { recursive: true });
  bytes += walk(from);
}
writeFileSync(
  join(out, "PACKAGE-CONTENTS.md"),
  [
    "# 分发包内容",
    "",
    "由 `npm run pack:skill` 从完整仓库导出，只含运行与重新构建所需文件。安装：`npm ci --omit=dev`（重新构建需完整 `npm ci` 后 `npm run build`）。",
    "",
    "未包含：tests、examples/acceptance、docs/quality、docs/research 的扫描件与校勘数据、scripts。`references/acceptance.md` 等维护文档中指向这些路径的链接在分发包内不可用；维护与验收请使用完整仓库。",
    "",
    ...include.map((rel) => `- ${rel}`),
    "",
  ].join("\n"),
);
console.log(JSON.stringify({ out, entries: include.length, bytes }));
